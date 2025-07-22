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

import yaml
import json
import os
import sys
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

import fabric as fabric_api
from utils import parse_freeform_config

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

# --- Utility Classes ---

class FabricBuilder:
    """Main class for building network fabrics."""
    
    def __init__(self):
        """Initialize the FabricBuilder with project paths."""
        self.script_dir = Path(__file__).parent.absolute()
        self.project_root = self.script_dir.parents[3]
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

# --- Helper Functions ---

def load_yaml_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Load a YAML file and return its content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file {filepath}: {e}")
        return None

def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file {filepath}: {e}")
        return None

def save_json_file(data: Dict[str, Any], filepath: str) -> bool:
    """Save data to a JSON file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)
        return True
    except Exception as e:
        print(f"Error saving JSON file {filepath}: {e}")
        return False

def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two configurations with override taking precedence."""
    if not isinstance(base_config, dict) or not isinstance(override_config, dict):
        return override_config if override_config else base_config
    
    merged = base_config.copy()
    for key, value in override_config.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    return merged

def read_freeform_config(file_path: str) -> str:
    """Read the content of a freeform configuration file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Freeform config file not found at {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading freeform config {file_path}: {e}")
        return ""

def get_template_name(fabric_type: str, template_mapping_file: str) -> Optional[str]:
    """Get the template name from the mapping file based on fabric type."""
    templates = load_yaml_file(template_mapping_file)
    if templates:
        return templates.get(fabric_type)
    return None

def validate_file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    return Path(filepath).exists()

def cleanup_temp_file(filepath: str) -> None:
    """Remove a temporary file safely."""
    try:
        if Path(filepath).exists():
            os.remove(filepath)
            print(f"Cleaned up temporary file: {filepath}")
    except Exception as e:
        print(f"Warning: Could not clean up {filepath}: {e}")

def validate_configuration_files(config: FabricConfig) -> bool:
    """Validate that all required configuration files exist."""
    required_files = [
        config.config_path,
        config.defaults_path,
        config.field_mapping_path,
        config.template_map_path
    ]
    
    missing_files = [f for f in required_files if not Path(f).exists()]
    
    if missing_files:
        print("❌ Missing required configuration files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    return True

def print_build_summary(fabric_type: str, fabric_name: str, success: bool) -> None:
    """Print a build summary message."""
    status = "✅ SUCCESS" if success else "❌ FAILED"
    print(f"\n{status}: {fabric_type} - {fabric_name}")
    if success:
        print(f"   Fabric '{fabric_name}' has been created successfully")
    else:
        print(f"   Failed to create fabric '{fabric_name}'")

def flatten_config(nested_config: Dict[str, Any], parent_key: str = '', separator: str = '_') -> Dict[str, Any]:
    """Flatten a nested dictionary into a single-level dictionary."""
    if not isinstance(nested_config, dict):
        return {parent_key: nested_config} if parent_key else {}
    
    items = []
    for key, value in nested_config.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_config(value, new_key, separator).items())
        else:
            items.append((new_key, value))
    return dict(items)

def apply_field_mapping(config: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
    """Apply field mapping to a configuration dictionary."""
    if not isinstance(mapping, dict):
        return config
    
    mapped_config = {}
    for key, value in config.items():
        if key in mapping and mapping[key] is not None:
            mapped_config[mapping[key]] = value
        elif key not in mapping:
            # Keep unmapped fields as-is
            mapped_config[key] = value
    return mapped_config

def get_nested_value(config_dict: Dict[str, Any], keys: Tuple[str, ...]) -> Any:
    """Get a nested value from a dictionary using a tuple of keys."""
    if not isinstance(config_dict, dict) or not keys:
        return None
    
    value = config_dict
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value

# --- Core Logic ---

class PayloadGenerator:
    """Handles the generation of API payloads for fabric creation."""
    
    @staticmethod
    def prepare_fabric_payload(config: FabricConfig) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Prepare the API payload for creating a fabric-like entity."""
        # Load configurations
        fabric_config = load_yaml_file(config.config_path)
        defaults_config = load_yaml_file(config.defaults_path)
        field_mapping = load_yaml_file(config.field_mapping_path)

        if not all([fabric_config, defaults_config, field_mapping]):
            print("Could not load required configurations or mappings. Exiting.")
            return None, None

        # Merge configurations
        final_config = PayloadGenerator._merge_all_configs(defaults_config, fabric_config)
        
        # Flatten and map configurations
        flat_config = flatten_config(final_config)
        mapped_config = apply_field_mapping(flat_config, flatten_config(field_mapping))

        # Get template name
        fabric_type = get_nested_value(fabric_config, config.type_keys)
        if not fabric_type:
            print(f"Fabric type not specified at '{'.'.join(config.type_keys)}' in the config.")
            return None, None

        template_name = get_template_name(fabric_type, config.template_map_path)
        if not template_name:
            print(f"Could not find a template for fabric type '{fabric_type}'.")
            return None, None

        # Prepare payload
        fabric_name = get_nested_value(fabric_config, config.name_keys)
        if not fabric_name:
            print(f"Fabric name not specified at '{'.'.join(config.name_keys)}' in the config.")
            return None, None

        # Build API payload
        api_payload = PayloadGenerator._build_api_payload(mapped_config, final_config, fabric_name, template_name)
        
        return api_payload, template_name

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
        # mapped_config["FABRIC_TYPE"] = template_name

        if "BGP_AS" in mapped_config:
            mapped_config["SITE_ID"] = mapped_config["BGP_AS"]

        return {
            "nvPairs": mapped_config,
            "vrfTemplate": vrf_template,
            "networkTemplate": network_template,
            "vrfExtensionTemplate": vrf_extension_template,
            "networkExtensionTemplate": network_extension_template
        }

    @staticmethod
    def add_freeform_content_to_payload(api_payload: Dict[str, Any], template_name: str, 
                                       freeform_paths: 'FreeformPaths') -> None:
        """Add freeform configuration content to the API payload."""
        nvpairs = api_payload["nvPairs"]
        
        if template_name == "Easy_Fabric":
            if freeform_paths.leaf and validate_file_exists(freeform_paths.leaf):
                nvpairs["EXTRA_CONF_LEAF"] = parse_freeform_config(freeform_paths.leaf)
            
            if freeform_paths.spine and validate_file_exists(freeform_paths.spine):
                nvpairs["EXTRA_CONF_SPINE"] = parse_freeform_config(freeform_paths.spine)
            
            if freeform_paths.aaa and validate_file_exists(freeform_paths.aaa):
                nvpairs["AAA_SERVER_CONF"] = parse_freeform_config(freeform_paths.aaa)
                
            if freeform_paths.banner and validate_file_exists(freeform_paths.banner):
                nvpairs["BANNER"] = parse_freeform_config(freeform_paths.banner)
        
        elif template_name == "External_Fabric":
            if freeform_paths.fabric and validate_file_exists(freeform_paths.fabric):
                nvpairs["FABRIC_FREEFORM"] = parse_freeform_config(freeform_paths.fabric)
                
            if freeform_paths.aaa and validate_file_exists(freeform_paths.aaa):
                nvpairs["AAA_SERVER_CONF"] = parse_freeform_config(freeform_paths.aaa)

# --- Builders ---

class FabricBuilderMethods:
    """Collection of methods for building different types of fabrics."""
    
    def __init__(self):
        self.builder = FabricBuilder()
        self.payload_generator = PayloadGenerator()
    
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
        print(f"\n=== Building VXLAN EVPN Fabric: {fabric_site_name} ===")
        
        try:
            # Get configuration and validate files
            config = self.builder.get_fabric_config(FabricType.VXLAN_EVPN, fabric_site_name)
            if not validate_configuration_files(config):
                return False
            
            # Generate payload
            api_payload, template_name = self.payload_generator.prepare_fabric_payload(config)
            if not api_payload or not template_name:
                print("Failed to generate payload for VXLAN EVPN fabric")
                return False
            
            # Get freeform paths and add content to payload
            freeform_paths = self.get_freeform_paths(fabric_site_name, FabricType.VXLAN_EVPN)
            self.payload_generator.add_freeform_content_to_payload(api_payload, template_name, freeform_paths)
            
            # Save payload and call API
            temp_payload_file = f"temp_payload_{fabric_site_name}.json"
            if not save_json_file(api_payload, temp_payload_file):
                return False
            
            print(f"Payload saved to {temp_payload_file}")
            print("Calling create_fabric API for VXLAN EVPN Fabric...")
            
            fabric_api.create_fabric(
                filename=temp_payload_file,
                template_name=template_name
            )
            
            cleanup_temp_file(temp_payload_file)
            print_build_summary("VXLAN EVPN Fabric", fabric_site_name, True)
            return True
            
        except Exception as e:
            print(f"❌ Error building VXLAN EVPN fabric {fabric_site_name}: {e}")
            print_build_summary("VXLAN EVPN Fabric", fabric_site_name, False)
            return False

    def build_multi_site_domain(self, msd_name: str) -> bool:
        """Build a Multi-Site Domain (MSD) configuration."""
        print(f"\n=== Building Multi-Site Domain: {msd_name} ===")
        
        try:
            # Get configuration and generate payload
            config = self.builder.get_fabric_config(FabricType.MULTI_SITE_DOMAIN, msd_name)
            api_payload, template_name = self.payload_generator.prepare_fabric_payload(config)
            
            if not api_payload or not template_name:
                print("Failed to generate payload for Multi-Site Domain")
                return False
            
            # Set MSD-specific parameters
            api_payload["nvPairs"]["FABRIC_TYPE"] = "MFD"
            api_payload["nvPairs"]["FF"] = "MSD"
            
            # Save payload and call API
            temp_payload_file = f"temp_payload_{msd_name}.json"
            if not save_json_file(api_payload, temp_payload_file):
                return False
            
            print(f"Payload saved to {temp_payload_file}")
            print("Calling create_fabric API for Multi-Site Domain...")
            
            fabric_api.create_fabric(
                filename=temp_payload_file,
                template_name=template_name
            )
            
            cleanup_temp_file(temp_payload_file)
            print(f"✅ Successfully built Multi-Site Domain: {msd_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error building Multi-Site Domain {msd_name}: {e}")
            return False

    def build_inter_site_network(self, isn_name: str) -> bool:
        """Build an Inter-Site Network (ISN) configuration."""
        print(f"\n=== Building Inter-Site Network: {isn_name} ===")
        
        try:
            # Get configuration and generate payload
            config = self.builder.get_fabric_config(FabricType.INTER_SITE_NETWORK, isn_name)
            api_payload, template_name = self.payload_generator.prepare_fabric_payload(config)
            
            if not api_payload or not template_name:
                print("Failed to generate payload for Inter-Site Network")
                return False
            
            # Set ISN-specific parameters
            api_payload["nvPairs"].pop("SITE_ID", None)  # Remove SITE_ID if it exists
            api_payload["nvPairs"]["FABRIC_TYPE"] = "External"
            api_payload["nvPairs"]["EXT_FABRIC_TYPE"] = "Multi-Site External Network"
            
            # Get freeform paths
            freeform_paths = self.get_freeform_paths(isn_name, FabricType.INTER_SITE_NETWORK)
            
            # Save payload and call API
            temp_payload_file = f"temp_payload_{isn_name}.json"
            if not save_json_file(api_payload, temp_payload_file):
                return False
            
            print(f"Payload saved to {temp_payload_file}")
            print("Calling create_fabric API for Inter-Site Network...")
            fabric_api.create_fabric(
                filename=temp_payload_file,
                template_name=template_name,
                aaa_freeform_config_file=freeform_paths.aaa,
                fabric_freeform_config_file=freeform_paths.fabric
            )
            
            cleanup_temp_file(temp_payload_file)
            print(f"✅ Successfully built Inter-Site Network: {isn_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error building Inter-Site Network {isn_name}: {e}")
            return False

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
    msd_to_build = "MSD-Test"
    isn_to_build = "ISN-Test"
    
    # --- Build Data Center VXLAN EVPN Fabric ---
    # Uncomment to build VXLAN EVPN fabric
    success = fabric_methods.build_vxlan_evpn_fabric(fabric_site_to_build)
    if not success:
        print(f"Failed to build VXLAN EVPN fabric: {fabric_site_to_build}")
        return 1

    # --- Build Multi-Site Domain ---
    # Uncomment to build Multi-Site Domain
    success = fabric_methods.build_multi_site_domain(msd_to_build)
    if not success:
        print(f"Failed to build Multi-Site Domain: {msd_to_build}")
        return 1

    # --- Build Inter-Site Network ---
    # Uncomment to build Inter-Site Network
    success = fabric_methods.build_inter_site_network(isn_to_build)
    if not success:
        print(f"Failed to build Inter-Site Network: {isn_to_build}")
        return 1

    # --- Link Fabrics ---
    # Uncomment to link fabrics
    # success = fabric_methods.link_fabrics(parent_fabric=msd_to_build, child_fabric=isn_to_build)
    # if not success:
    #     print(f"Failed to link fabrics: {child_fabric} -> {parent_fabric}")
    #     return 1
    
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
