#!/usr/bin/env python3
"""
Fabric Builder - Automated Network Fabric Configuration Tool

This module provides functionality to build different types of network fabrics:
- Data Center VXLAN EVPN Fabrics
- Multi-Site Domains (MSD)
- Inter-Site Networks (ISN)

It handles configuration merging, field mapping, and API payload generation
for Cisco NDFC fabric management.
"""

import os
import sys
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

import api.fabric as fabric_api
from config_utils import (
    load_yaml_file, load_json_file, merge_configs, 
    read_freeform_config, apply_field_mapping, 
    get_nested_value, extract_child_fabrics_config,
    print_build_summary, validate_file_exists, 
    validate_configuration_files, flatten_config,
    get_template_name
)

# --- Constants and Enums ---

class FabricType(Enum):
    """Enumeration of supported fabric types."""
    VXLAN_EVPN = "VXLAN_EVPN"
    MULTI_SITE_DOMAIN = "MSD"
    INTER_SITE_NETWORK = "ISN"

@dataclass
class FabricConfig:
    """Configuration paths and parameters for fabric building."""
    config_path: str
    defaults_path: str
    field_mapping_path: str
    template_map_path: str
    type_keys: Tuple[str, ...]
    name_keys: Tuple[str, ...]

@dataclass
class FreeformPaths:
    """Paths to freeform configuration files."""
    aaa: str = ""
    leaf: str = ""
    spine: str = ""
    banner: str = ""
    fabric: str = ""

@dataclass
class ChildFabrics:
    """Container for child fabric information."""
    regular_fabrics: List[str]
    isn_fabrics: List[str]
    
    def get_all_child_fabrics(self) -> List[str]:
        """Get a list of all child fabrics (both regular and ISN)."""
        return self.regular_fabrics + self.isn_fabrics

# --- Utility Classes ---

class FabricBuilder:
    """Main class for building network fabrics."""
    
    def __init__(self):
        """Initialize the FabricBuilder with project paths."""
        self.script_dir = Path(__file__).parent.absolute()
        self.project_root = self.script_dir.parents[2]
        self.resources_dir = self.script_dir / "resources"
    
    def get_fabric_config(self, fabric_type: FabricType, name: str) -> FabricConfig:
        """Get configuration paths for a specific fabric type."""
        base_configs = {
            FabricType.VXLAN_EVPN: FabricConfig(
                config_path=str(self.project_root / "network_configs" / "1_vxlan_evpn" / "fabric" / f"{name}.yaml"),
                defaults_path=str(self.resources_dir / "corp_defaults" / "cisco_vxlan.yaml"),
                field_mapping_path=str(self.resources_dir / "_field_mapping" / "cisco_vxlan.yaml"),
                template_map_path=str(self.resources_dir / "fabric_template.yaml"),
                type_keys=('Fabric', 'type'),
                name_keys=('Fabric', 'name')
            ),
            FabricType.MULTI_SITE_DOMAIN: FabricConfig(
                config_path=str(self.project_root / "network_configs" / "1_vxlan_evpn" / "multisite_deployment" / f"{name}.yaml"),
                defaults_path=str(self.resources_dir / "corp_defaults" / "cisco_multi-site.yaml"),
                field_mapping_path=str(self.resources_dir / "_field_mapping" / "cisco_multi-site.yaml"),
                template_map_path=str(self.resources_dir / "fabric_template.yaml"),
                type_keys=('Fabric', 'type'),
                name_keys=('Fabric', 'name')
            ),
            FabricType.INTER_SITE_NETWORK: FabricConfig(
                config_path=str(self.project_root / "network_configs" / "1_vxlan_evpn" / "inter-site_network" / f"{name}.yaml"),
                defaults_path=str(self.resources_dir / "corp_defaults" / "cisco_inter-site.yaml"),
                field_mapping_path=str(self.resources_dir / "_field_mapping" / "cisco_inter-site.yaml"),
                template_map_path=str(self.resources_dir / "fabric_template.yaml"),
                type_keys=('Fabric', 'type'),
                name_keys=('Fabric', 'name')
            )
        }
        return base_configs[fabric_type]

# --- Main Fabric Building Functions ---

class PayloadGenerator:
    """Handles the generation of API payloads for fabric creation."""
    
    @staticmethod
    def prepare_fabric_payload(config: FabricConfig) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
        """Prepare the API payload for creating a fabric-like entity."""
        # Extract fabric name from filename
        config_file = Path(config.config_path)
        fabric_name = config_file.stem  # Gets filename without extension
        # print(f"Using fabric name from filename: {fabric_name}")
        
        # Load configurations
        fabric_config = load_yaml_file(config.config_path)
        defaults_config = load_yaml_file(config.defaults_path)
        field_mapping = load_yaml_file(config.field_mapping_path)

        if not all([fabric_config, defaults_config, field_mapping]):
            print("Could not load required configurations or mappings. Exiting.")
            return None, None, None

        # Merge configurations
        final_config = PayloadGenerator._merge_all_configs(defaults_config, fabric_config)
        
        # Flatten and map configurations
        flat_config = flatten_config(final_config)
        mapped_config = apply_field_mapping(flat_config, flatten_config(field_mapping))

        # Get template name
        fabric_type = get_nested_value(fabric_config, config.type_keys)
        if not fabric_type:
            print(f"Fabric type not specified at '{'.'.join(config.type_keys)}' in the config.")
            return None, None, None

        template_name = get_template_name(fabric_type, config.template_map_path)
        if not template_name:
            print(f"Could not find a template for fabric type '{fabric_type}'.")
            return None, None, None

        # Build API payload using filename as fabric name
        api_payload = PayloadGenerator._build_api_payload(mapped_config, final_config, fabric_name, template_name)
        
        return api_payload, template_name, fabric_name

    @staticmethod
    def _merge_all_configs(defaults_config: Dict[str, Any], fabric_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge default and fabric configurations."""
        final_config = {}
        for key in defaults_config:
            if key in fabric_config:
                final_config[key] = merge_configs(defaults_config[key], fabric_config[key])
            else:
                final_config[key] = defaults_config[key]
        return final_config

    @staticmethod
    def _build_api_payload(mapped_config: Dict[str, Any], final_config: Dict[str, Any], 
                          fabric_name: str, template_name: str) -> Dict[str, Any]:
        """Build the final API payload."""
        # Get template configurations
        advanced_config = final_config.get('Advanced', {})
        vrf_template = advanced_config.get('VRF Template', "Default_VRF_Universal")
        network_template = advanced_config.get('Network Template', "Default_Network_Universal")
        vrf_extension_template = advanced_config.get('VRF Extension Template', "Default_VRF_Extension_Universal")
        network_extension_template = advanced_config.get('Network Extension Template', "Default_Network_Extension_Universal")

        # Clean up mapped config
        template_keys = ['vrfTemplate', 'networkTemplate', 'vrfExtensionTemplate', 'networkExtensionTemplate']
        for key in template_keys:
            mapped_config.pop(key, None)

        # Set required fields
        mapped_config["FABRIC_NAME"] = fabric_name

        if "BGP_AS" in mapped_config:
            mapped_config["SITE_ID"] = mapped_config["BGP_AS"]

        return mapped_config

    @staticmethod
    def add_freeform_content_to_payload(payload_data: Dict[str, Any], template_name: str, 
                                       freeform_paths: 'FreeformPaths') -> None:
        """Add freeform configuration content to the API payload."""
        if template_name == "Easy_Fabric":
            if freeform_paths.leaf and validate_file_exists(freeform_paths.leaf):
                payload_data["EXTRA_CONF_LEAF"] = read_freeform_config(freeform_paths.leaf)
            
            if freeform_paths.spine and validate_file_exists(freeform_paths.spine):
                payload_data["EXTRA_CONF_SPINE"] = read_freeform_config(freeform_paths.spine)
            
            if freeform_paths.aaa and validate_file_exists(freeform_paths.aaa):
                payload_data["AAA_SERVER_CONF"] = read_freeform_config(freeform_paths.aaa)
                
            if freeform_paths.banner and validate_file_exists(freeform_paths.banner):
                payload_data["BANNER"] = read_freeform_config(freeform_paths.banner)
        
        elif template_name == "External_Fabric":
            if freeform_paths.fabric and validate_file_exists(freeform_paths.fabric):
                payload_data["FABRIC_FREEFORM"] = read_freeform_config(freeform_paths.fabric)
                
            if freeform_paths.aaa and validate_file_exists(freeform_paths.aaa):
                payload_data["AAA_SERVER_CONF"] = read_freeform_config(freeform_paths.aaa)

# --- Builders ---

class FabricBuilderMethods:
    """Collection of methods for building different types of fabrics."""
    
    def __init__(self):
        self.builder = FabricBuilder()
        self.payload_generator = PayloadGenerator()
    
    def _get_fabric_specific_params(self, fabric_type: FabricType, payload_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get fabric-type specific parameters and modifications."""
        if fabric_type == FabricType.MULTI_SITE_DOMAIN:
            payload_data["FABRIC_TYPE"] = "MFD"
            payload_data["FF"] = "MSD"
        elif fabric_type == FabricType.INTER_SITE_NETWORK:
            payload_data.pop("SITE_ID", None)  # Remove SITE_ID if it exists
            payload_data["FABRIC_TYPE"] = "External"
            payload_data["EXT_FABRIC_TYPE"] = "Multi-Site External Network"
        
        return payload_data
    
    def _execute_fabric_operation(self, fabric_name: str, fabric_type: FabricType, operation: str = "create") -> bool:
        """
        Execute fabric operation (create or update) for any fabric type.
        
        Args:
            fabric_name: Name of the fabric
            fabric_type: Type of fabric to operate on
            operation: "create" or "update"
            
        Returns:
            bool: True if successful, False otherwise
        """
        operation_verb = "Building" if operation == "create" else "Updating"
        past_verb = "built" if operation == "create" else "updated"
        
        type_names = {
            FabricType.VXLAN_EVPN: "VXLAN EVPN Fabric",
            FabricType.MULTI_SITE_DOMAIN: "Multi-Site Domain",
            FabricType.INTER_SITE_NETWORK: "Inter-Site Network"
        }
        
        type_name = type_names.get(fabric_type, str(fabric_type))
        print(f"\n=== {operation_verb} {type_name}: {fabric_name} ===")
        
        try:
            # Get configuration and validate files for VXLAN EVPN
            config = self.builder.get_fabric_config(fabric_type, fabric_name)
            
            if fabric_type == FabricType.VXLAN_EVPN:
                required_files = [
                    config.config_path, config.defaults_path, 
                    config.field_mapping_path, config.template_map_path
                ]
                files_exist, missing_files = validate_configuration_files(required_files)
                if not files_exist:
                    print("❌ Missing required configuration files:")
                    for file in missing_files:
                        print(f"   - {file}")
                    return False
            
            # Generate payload
            payload_data, template_name, fabric_name_from_file = self.payload_generator.prepare_fabric_payload(config)
            if not payload_data or not template_name or not fabric_name_from_file:
                print(f"Failed to generate payload for {type_name} {operation}")
                return False
            
            # Apply fabric-specific parameters
            payload_data = self._get_fabric_specific_params(fabric_type, payload_data)
            
            # Get freeform paths and add content to payload (for VXLAN_EVPN and ISN)
            if fabric_type in [FabricType.VXLAN_EVPN, FabricType.INTER_SITE_NETWORK]:
                freeform_paths = self.get_freeform_paths(fabric_name, fabric_type)
                self.payload_generator.add_freeform_content_to_payload(payload_data, template_name, freeform_paths)
            
            print(f"Calling {operation}_fabric API for {type_name}...")
            
            # Call appropriate fabric API
            if operation == "create":
                success = fabric_api.create_fabric(
                    fabric_name=fabric_name_from_file,
                    template_name=template_name,
                    payload_data=payload_data
                )
            else:  # update
                success = fabric_api.update_fabric(
                    fabric_name=fabric_name_from_file,
                    template_name=template_name,
                    payload_data=payload_data
                )
            
            if success:
                operation_suffix = " Update" if operation == "update" else ""
                print_build_summary(f"{type_name}{operation_suffix}", fabric_name, True, past_verb if operation == "update" else "created")
                return True
            else:
                operation_suffix = " Update" if operation == "update" else ""
                print_build_summary(f"{type_name}{operation_suffix}", fabric_name, False, past_verb if operation == "update" else "created")
                return False
                
        except Exception as e:
            print(f"❌ Error {operation}ing {type_name} {fabric_name}: {e}")
            operation_suffix = " Update" if operation == "update" else ""
            print_build_summary(f"{type_name}{operation_suffix}", fabric_name, False, past_verb if operation == "update" else "created")
            return False
    
    def get_freeform_paths(self, fabric_name: str, fabric_type: FabricType) -> FreeformPaths:
        """Get freeform configuration file paths for a fabric."""
        freeform_paths = FreeformPaths()
        resources_freeform_dir = self.builder.resources_dir / "freeform"
        
        if fabric_type == FabricType.VXLAN_EVPN:
            # Check for fabric-specific freeform configs first
            fabric_freeform_dir = (self.builder.project_root / "network_configs" / 
                                 "1_vxlan_evpn" / "fabric" / f"{fabric_name}_FreeForm")
            
            # Default paths
            freeform_paths.aaa = str(resources_freeform_dir / "AAA Freeform Config.sh")
            freeform_paths.leaf = str(resources_freeform_dir / "Leaf Freeform Config.sh")
            freeform_paths.spine = str(resources_freeform_dir / "Spine Freeform Config.sh")
            freeform_paths.banner = str(resources_freeform_dir / "Banner.sh")
            
            # Override with fabric-specific configs if they exist
            if fabric_freeform_dir.exists():
                for config_type, filename in [
                    ("aaa", "AAA Freeform Config.sh"),
                    ("leaf", "Leaf Freeform Config.sh"),
                    ("spine", "Spine Freeform Config.sh"),
                    ("banner", "Banner.sh")
                ]:
                    fabric_specific_path = fabric_freeform_dir / filename
                    if fabric_specific_path.exists():
                        setattr(freeform_paths, config_type, str(fabric_specific_path))
        
        elif fabric_type == FabricType.INTER_SITE_NETWORK:
            # Load from defaults configuration
            defaults_path = self.builder.get_fabric_config(fabric_type, fabric_name).defaults_path
            defaults_config = load_yaml_file(defaults_path)
            
            if defaults_config:
                advanced_config = defaults_config.get('Advanced', {})
                
                fabric_freeform = advanced_config.get('Fabric Freeform', {}).get('freeform')
                if fabric_freeform:
                    freeform_paths.fabric = str(resources_freeform_dir / Path(fabric_freeform).name)
                
                aaa_freeform = advanced_config.get('AAA Freeform Config', {}).get('freeform')
                if aaa_freeform:
                    freeform_paths.aaa = str(resources_freeform_dir / Path(aaa_freeform).name)
        
        return freeform_paths

    def build_vxlan_evpn_fabric(self, fabric_site_name: str) -> bool:
        """Build a VXLAN EVPN fabric configuration."""
        return self._execute_fabric_operation(fabric_site_name, FabricType.VXLAN_EVPN, "create")

    def build_multi_site_domain(self, msd_name: str) -> bool:
        """Build a Multi-Site Domain (MSD) configuration."""
        return self._execute_fabric_operation(msd_name, FabricType.MULTI_SITE_DOMAIN, "create")

    def build_inter_site_network(self, isn_name: str) -> bool:
        """Build an Inter-Site Network (ISN) configuration."""
        return self._execute_fabric_operation(isn_name, FabricType.INTER_SITE_NETWORK, "create")

    def update_vxlan_evpn_fabric(self, fabric_site_name: str) -> bool:
        """Update an existing VXLAN EVPN fabric configuration."""
        return self._execute_fabric_operation(fabric_site_name, FabricType.VXLAN_EVPN, "update")

    def update_multi_site_domain(self, msd_name: str) -> bool:
        """Update an existing Multi-Site Domain (MSD) configuration."""
        return self._execute_fabric_operation(msd_name, FabricType.MULTI_SITE_DOMAIN, "update")

    def update_inter_site_network(self, isn_name: str) -> bool:
        """Update an existing Inter-Site Network (ISN) configuration."""
        return self._execute_fabric_operation(isn_name, FabricType.INTER_SITE_NETWORK, "update")

    def _get_child_fabrics_from_msd_config(self, msd_name: str) -> Optional[ChildFabrics]:
        """Load child fabric information from MSD configuration file."""
        try:
            config = self.builder.get_fabric_config(FabricType.MULTI_SITE_DOMAIN, msd_name)
            fabric_config = load_yaml_file(config.config_path)
            
            if not fabric_config:
                print(f"Failed to load configuration for MSD '{msd_name}'")
                return None
            
            # Extract child fabric information
            child_fabrics_info = extract_child_fabrics_config(fabric_config)
            return ChildFabrics(
                regular_fabrics=child_fabrics_info.get("regular_fabrics", []),
                isn_fabrics=child_fabrics_info.get("isn_fabrics", [])
            )
        except Exception as e:
            print(f"❌ Error loading child fabrics configuration for MSD {msd_name}: {e}")
            return None

    def _execute_msd_child_fabric_operation(self, msd_name: str, operation: str) -> bool:
        """
        Execute add or remove operation for child fabrics in MSD.
        
        Args:
            msd_name: Name of the MSD
            operation: "add" or "remove"
            
        Returns:
            bool: True if successful, False otherwise
        """
        operation_verb = "Adding" if operation == "add" else "Removing"
        operation_preposition = "to" if operation == "add" else "from"
        
        print(f"\n=== {operation_verb} Child Fabrics {operation_preposition} MSD: {msd_name} ===")
        
        # Load child fabric configuration
        child_fabrics = self._get_child_fabrics_from_msd_config(msd_name)
        if not child_fabrics:
            return False
        
        print(f"Found child fabrics: Regular={child_fabrics.regular_fabrics}, ISN={child_fabrics.isn_fabrics}")
        
        if not child_fabrics.get_all_child_fabrics():
            print(f"No child fabrics found in configuration for MSD '{msd_name}'")
            return True
        
        # Execute operation on each child fabric
        all_success = True
        all_child_fabrics = child_fabrics.get_all_child_fabrics()
        
        for child_fabric in all_child_fabrics:
            try:
                print(f"{operation_verb} child fabric '{child_fabric}' {operation_preposition} MSD '{msd_name}'...")
                
                if operation == "add":
                    fabric_api.add_MSD(parent_fabric_name=msd_name, child_fabric_name=child_fabric)
                    print(f"✅ Successfully added '{child_fabric}' to '{msd_name}'")
                else:  # remove
                    fabric_api.remove_MSD(parent_fabric_name=msd_name, child_fabric_name=child_fabric)
                    print(f"✅ Successfully removed '{child_fabric}' from '{msd_name}'")
                    
            except Exception as e:
                print(f"❌ Failed to {operation} '{child_fabric}' {operation_preposition} '{msd_name}': {e}")
                all_success = False
        
        if all_success:
            action_past = "added to" if operation == "add" else "removed from"
            print(f"✅ All child fabrics successfully {action_past} MSD '{msd_name}'")
        else:
            action_past = "be added to" if operation == "add" else "be removed from"
            print(f"⚠️  Some child fabrics failed to {action_past} MSD '{msd_name}'")
        
        return all_success

    def add_child_fabrics_to_msd(self, msd_name: str) -> bool:
        """Add child fabrics to an MSD based on its configuration file."""
        return self._execute_msd_child_fabric_operation(msd_name, "add")

    def remove_child_fabrics_from_msd(self, msd_name: str) -> bool:
        """Remove child fabrics from an MSD based on its configuration file."""
        return self._execute_msd_child_fabric_operation(msd_name, "remove")

    def link_fabrics(self, parent_fabric: str, child_fabric: str) -> bool:
        """Link a child fabric to a parent fabric."""
        print(f"\n=== Linking {child_fabric} to {parent_fabric} ===")
        
        try:
            fabric_api.add_MSD(parent_fabric_name=parent_fabric, child_fabric_name=child_fabric)
            print(f"✅ Successfully linked {child_fabric} to {parent_fabric}")
            return True
        except Exception as e:
            print(f"❌ Error linking fabrics: {e}")
            return False

    def _determine_fabric_type_from_file(self, fabric_name: str) -> Optional[FabricType]:
        """
        Determine the fabric type by reading the YAML configuration file.
        
        Args:
            fabric_name: Name of the fabric configuration file (without .yaml extension)
            
        Returns:
            FabricType or None if type cannot be determined
        """
        # Try each possible fabric type configuration path
        possible_paths = [
            (FabricType.VXLAN_EVPN, str(self.builder.project_root / "network_configs" / "1_vxlan_evpn" / "fabric" / f"{fabric_name}.yaml")),
            (FabricType.MULTI_SITE_DOMAIN, str(self.builder.project_root / "network_configs" / "1_vxlan_evpn" / "multisite_deployment" / f"{fabric_name}.yaml")),
            (FabricType.INTER_SITE_NETWORK, str(self.builder.project_root / "network_configs" / "1_vxlan_evpn" / "inter-site_network" / f"{fabric_name}.yaml"))
        ]
        
        for fabric_type, config_path in possible_paths:
            if validate_file_exists(config_path):
                fabric_config = load_yaml_file(config_path)
                if fabric_config:
                    config_type = get_nested_value(fabric_config, ('Fabric', 'type'))
                    if config_type:
                        # print(f"Found fabric type in {config_path}: {config_type}")
                        
                        # Map the type string from YAML to FabricType enum
                        type_mapping = {
                            "Data Center VXLAN EVPN": FabricType.VXLAN_EVPN,
                            "VXLAN EVPN Multi-Site": FabricType.MULTI_SITE_DOMAIN,
                            "Multi-Site Interconnect Network": FabricType.INTER_SITE_NETWORK
                        }
                        
                        if config_type in type_mapping:
                            determined_type = type_mapping[config_type]
                            # print(f"Mapped to FabricType: {determined_type}")
                            return determined_type
                        else:
                            print(f"⚠️  Unknown fabric type in config: {config_type}")
        
        print(f"❌ Could not determine fabric type for: {fabric_name}")
        return None

    def update_fabric(self, fabric_name: str) -> bool:
        """
        Generic method to update any type of fabric.
        Determines the fabric type from the YAML configuration file.
        
        Args:
            fabric_name: Name of the fabric configuration file (without .yaml extension)
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Determine fabric type from the configuration file
        fabric_type = self._determine_fabric_type_from_file(fabric_name)
        if not fabric_type:
            print(f"❌ Cannot determine fabric type for: {fabric_name}")
            return False
        
        # print(f"Updating fabric '{fabric_name}' of type: {fabric_type}")
        
        if fabric_type == FabricType.VXLAN_EVPN:
            return self.update_vxlan_evpn_fabric(fabric_name)
        elif fabric_type == FabricType.MULTI_SITE_DOMAIN:
            return self.update_multi_site_domain(fabric_name)
        elif fabric_type == FabricType.INTER_SITE_NETWORK:
            return self.update_inter_site_network(fabric_name)
        else:
            print(f"❌ Unsupported fabric type: {fabric_type}")
            return False

    def build_fabric(self, fabric_name: str) -> bool:
        """
        Generic method to build any type of fabric.
        Determines the fabric type from the YAML configuration file.
        
        Args:
            fabric_name: Name of the fabric configuration file (without .yaml extension)
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Determine fabric type from the configuration file
        fabric_type = self._determine_fabric_type_from_file(fabric_name)
        if not fabric_type:
            print(f"❌ Cannot determine fabric type for: {fabric_name}")
            return False
        
        print(f"Building fabric '{fabric_name}' of type: {fabric_type}")
        
        if fabric_type == FabricType.VXLAN_EVPN:
            return self.build_vxlan_evpn_fabric(fabric_name)
        elif fabric_type == FabricType.MULTI_SITE_DOMAIN:
            return self.build_multi_site_domain(fabric_name)
        elif fabric_type == FabricType.INTER_SITE_NETWORK:
            return self.build_inter_site_network(fabric_name)
        else:
            print(f"❌ Unsupported fabric type: {fabric_type}")
            return False

def main():
    """
    Main function to run the fabric build process.
    Uncomment the section you want to run.
    """
    # Initialize the fabric builder
    fabric_methods = FabricBuilderMethods()
    
    print("🏗️  Fabric Builder - Automated Network Fabric Configuration Tool")
    print("=" * 70)
    
    # Configuration - Update these values as needed
    fabric_site_to_build = "Site3-Test"
    msd_to_build = "MSD-Test_15"
    isn_to_build = "ISN-Test"
    
    # --- Generic Build Method (reads fabric type from YAML files) ---
    
    # Build VXLAN EVPN fabric using generic method (fabric type determined from YAML)
    # success = fabric_methods.build_fabric(fabric_site_to_build)
    # if not success:
    #     print(f"Failed to build fabric: {fabric_site_to_build}")
    #     return 1
    
    # # Build Multi-Site Domain using generic method (fabric type determined from YAML)
    # success = fabric_methods.build_fabric(msd_to_build)
    # if not success:
    #     print(f"Failed to build fabric: {msd_to_build}")
    #     return 1
    
    # # Build Inter-Site Network using generic method (fabric type determined from YAML)
    # success = fabric_methods.build_fabric(isn_to_build)
    # if not success:
    #     print(f"Failed to build fabric: {isn_to_build}")
    #     return 1

    # # --- Add Child Fabrics to MSD ---
    # # Uncomment to add child fabrics to the MSD
    # success = fabric_methods.add_child_fabrics_to_msd(msd_to_build)
    # if not success:
    #     print(f"Failed to add child fabrics to MSD: {msd_to_build}")
    #     return 1
    
    # --- Update Existing Fabrics ---
    # Uncomment to update existing fabrics instead of creating new ones
    
    # Update VXLAN EVPN fabric (fabric type determined from YAML)
    success = fabric_methods.update_fabric(fabric_site_to_build)
    if not success:
        print(f"Failed to update fabric: {fabric_site_to_build}")
        return 1
    
    # Update Multi-Site Domain (fabric type determined from YAML)
    success = fabric_methods.update_fabric(msd_to_build)
    if not success:
        print(f"Failed to update fabric: {msd_to_build}")
        return 1
    
    # Update Inter-Site Network (fabric type determined from YAML)
    success = fabric_methods.update_fabric(isn_to_build)
    if not success:
        print(f"Failed to update fabric: {isn_to_build}")
        return 1
    
    # Alternative: Use specific update methods if preferred
    # success = fabric_methods.update_vxlan_evpn_fabric(fabric_site_to_build)
    # success = fabric_methods.update_multi_site_domain(msd_to_build) 
    # success = fabric_methods.update_inter_site_network(isn_to_build)
    
    print("\n🎉 Fabric build process completed successfully!")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
