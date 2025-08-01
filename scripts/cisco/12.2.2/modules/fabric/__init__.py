#!/usr/bin/env python3
"""
Fabric Builder Module - Core Components

This module provides the core functionality for building and managing network fabrics:
- Data Center VXLAN EVPN Fabrics
- Multi-Site Domains (MSD)
- Inter-Site Networks (ISN)

It handles configuration merging, field mapping, and API payload generation
for Cisco NDFC fabric management.
"""

import sys
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from modules.config_utils import (
    load_yaml_file, merge_configs, 
    read_freeform_config, apply_field_mapping, 
    get_nested_value,
    validate_file_exists, 
    flatten_config
)
from config.config_factory import config_factory

# --- Constants and Enums ---

class FabricType(Enum):
    """Enumeration of supported fabric types."""
    VXLAN_EVPN = "Easy_Fabric"
    MULTI_SITE_DOMAIN = "MSD_Fabric"
    INTER_SITE_NETWORK = "External_Fabric"
    
    @classmethod
    def from_yaml_type(cls, yaml_type: str) -> Optional['FabricType']:
        """Convert YAML fabric type string to FabricType enum."""
        yaml_to_enum_mapping = {
            "Data Center VXLAN EVPN": cls.VXLAN_EVPN,
            "VXLAN EVPN Multi-Site": cls.MULTI_SITE_DOMAIN,
            "Multi-Site Interconnect Network": cls.INTER_SITE_NETWORK
        }
        return yaml_to_enum_mapping.get(yaml_type)

@dataclass
class FabricConfig:
    """Configuration paths and parameters for fabric building."""
    config_path: str
    defaults_path: str
    field_mapping_path: str

@dataclass
class FreeformPaths:
    """Paths to freeform configuration files."""
    aaa: str = ""
    leaf: str = ""
    spine: str = ""
    banner: str = ""
    fabric: str = ""
    intra_links: str = ""

# --- Utility Classes ---

class FabricBuilder:
    """Main class for building network fabrics."""
    
    def __init__(self):
        """Initialize the FabricBuilder with centralized path configuration."""
        pass
    
    def get_fabric_config(self, fabric_type: FabricType, name: str) -> FabricConfig:
        """Get configuration paths for a specific fabric type."""
        fabric_paths = config_factory.get_fabric_paths()
        
        base_configs = {
            FabricType.VXLAN_EVPN: FabricConfig(
                config_path=str(fabric_paths['configs'] / f"{name}.yaml"),
                defaults_path=str(fabric_paths['defaults'].parent / "cisco_vxlan.yaml"),
                field_mapping_path=str(fabric_paths['field_mapping'].parent / "cisco_vxlan.yaml")
            ),
            FabricType.MULTI_SITE_DOMAIN: FabricConfig(
                config_path=str(fabric_paths['multisite'] / f"{name}.yaml"),
                defaults_path=str(fabric_paths['defaults'].parent / "cisco_multi-site.yaml"),
                field_mapping_path=str(fabric_paths['field_mapping'].parent / "cisco_multi-site.yaml")
            ),
            FabricType.INTER_SITE_NETWORK: FabricConfig(
                config_path=str(fabric_paths['inter_site'] / f"{name}.yaml"),
                defaults_path=str(fabric_paths['defaults'].parent / "cisco_inter-site.yaml"),
                field_mapping_path=str(fabric_paths['field_mapping'].parent / "cisco_inter-site.yaml")
            )
        }
        return base_configs[fabric_type]

class PayloadGenerator:
    """Handles the generation of API payloads for fabric creation."""
    
    @staticmethod
    def prepare_fabric_payload(config: FabricConfig) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
        """Prepare the API payload for creating a fabric-like entity."""
        # Extract fabric name from filename
        config_file = Path(config.config_path)
        fabric_name = config_file.stem  # Gets filename without extension
        
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

        # Get template name based on fabric type (use FabricType value directly)
        fabric_type_str = get_nested_value(fabric_config, ('Fabric', 'type'))
        if not fabric_type_str:
            print(f"Fabric type not specified at 'Fabric.type' in the config.")
            return None, None, None

        # Map fabric type string to FabricType enum and get template name
        fabric_enum = FabricType.from_yaml_type(fabric_type_str)
        if not fabric_enum:
            print(f"Could not determine template for fabric type '{fabric_type_str}'.")
            return None, None, None
            
        template_name = fabric_enum.value  # Template name is now the enum value

        # Build API payload using filename as fabric name
        api_payload = PayloadGenerator._build_api_payload(mapped_config, fabric_name, fabric_enum)
        
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
    def _build_api_payload(mapped_config: Dict[str, Any], fabric_name: str, fabric_type: FabricType) -> Dict[str, Any]:
        """Build the final API payload with all necessary modifications."""
        # Clean up mapped config - remove VRF/Network template settings
        template_keys = ['vrfTemplate', 'networkTemplate', 'vrfExtensionTemplate', 'networkExtensionTemplate']
        for key in template_keys:
            mapped_config.pop(key, None)

        # Set required fields
        mapped_config["FABRIC_NAME"] = fabric_name

        if "BGP_AS" in mapped_config:
            mapped_config["SITE_ID"] = mapped_config["BGP_AS"]

        # Apply fabric-type specific modifications
        if fabric_type == FabricType.MULTI_SITE_DOMAIN:
            mapped_config["FABRIC_TYPE"] = "MFD"
            mapped_config["FF"] = "MSD"
        elif fabric_type == FabricType.INTER_SITE_NETWORK:
            mapped_config.pop("SITE_ID", None)  # Remove SITE_ID if it exists
            mapped_config["FABRIC_TYPE"] = "External"
            mapped_config["EXT_FABRIC_TYPE"] = "Multi-Site External Network"

        return mapped_config

    @staticmethod
    def add_freeform_content_to_payload(payload_data: Dict[str, Any], template_name: str, 
                                       freeform_paths: 'FreeformPaths') -> None:
        """Add freeform configuration content to the API payload."""
        if template_name == FabricType.VXLAN_EVPN.value:
            if freeform_paths.leaf and validate_file_exists(freeform_paths.leaf):
                payload_data["EXTRA_CONF_LEAF"] = read_freeform_config(freeform_paths.leaf)
            
            if freeform_paths.spine and validate_file_exists(freeform_paths.spine):
                payload_data["EXTRA_CONF_SPINE"] = read_freeform_config(freeform_paths.spine)
            
            if freeform_paths.intra_links and validate_file_exists(freeform_paths.intra_links):
                payload_data["EXTRA_CONF_INTRA_LINKS"] = read_freeform_config(freeform_paths.intra_links)
            
            if freeform_paths.aaa and validate_file_exists(freeform_paths.aaa):
                payload_data["AAA_SERVER_CONF"] = read_freeform_config(freeform_paths.aaa)
                
            if freeform_paths.banner and validate_file_exists(freeform_paths.banner):
                payload_data["BANNER"] = "`" + read_freeform_config(freeform_paths.banner) + "`"

        elif template_name == FabricType.INTER_SITE_NETWORK.value:
            if freeform_paths.fabric and validate_file_exists(freeform_paths.fabric):
                payload_data["FABRIC_FREEFORM"] = read_freeform_config(freeform_paths.fabric)
                
            if freeform_paths.aaa and validate_file_exists(freeform_paths.aaa):
                payload_data["AAA_SERVER_CONF"] = read_freeform_config(freeform_paths.aaa)

class BaseFabricMethods:
    """Base class with shared methods for fabric operations."""
    
    def __init__(self):
        self.builder = FabricBuilder()
        self.payload_generator = PayloadGenerator()
    
    def get_freeform_paths(self, fabric_name: str, fabric_type: FabricType) -> FreeformPaths:
        """Get freeform configuration file paths for a fabric."""
        freeform_paths = FreeformPaths()
        fabric_paths = config_factory.get_fabric_paths()
        resources_freeform_dir = fabric_paths['freeform']
        
        if fabric_type == FabricType.VXLAN_EVPN:
            # Load fabric configuration to get custom freeform paths
            fabric_config_path = self.builder.get_fabric_config(fabric_type, fabric_name).config_path
            fabric_config = load_yaml_file(fabric_config_path)
            
            # Check for fabric-specific freeform configs first
            fabric_freeform_dir = fabric_paths['configs'] / f"{fabric_name}_FreeForm"
            
            # Default paths
            freeform_paths.aaa = str(resources_freeform_dir / "AAA Freeform Config.sh")
            freeform_paths.leaf = str(resources_freeform_dir / "Leaf Freeform Config.sh")
            freeform_paths.spine = str(resources_freeform_dir / "Spine Freeform Config.sh")
            freeform_paths.banner = str(resources_freeform_dir / "Banner.sh")
            freeform_paths.intra_links = str(resources_freeform_dir / "Intra-fabric Links Additional Config.sh")
            
            # Override with paths from fabric configuration YAML if specified
            if fabric_config:
                # Check for AAA Freeform Config in Manageability section first
                manageability_config = fabric_config.get('Manageability', {})
                aaa_config = manageability_config.get('AAA Freeform Config', {})
                if isinstance(aaa_config, dict) and 'Freeform' in aaa_config:
                    aaa_path = aaa_config['Freeform']
                    freeform_paths.aaa = str(fabric_freeform_dir / f"{aaa_path}.sh")
                
                # Then check Advanced section
                advanced_config = fabric_config.get('Advanced', {})
                
                # Check for AAA Freeform Config in Advanced (fallback)
                if not freeform_paths.aaa or freeform_paths.aaa == str(resources_freeform_dir / "AAA Freeform Config.sh"):
                    aaa_advanced_config = advanced_config.get('AAA Freeform Config', {})
                    if isinstance(aaa_advanced_config, dict) and 'Freeform' in aaa_advanced_config:
                        aaa_path = aaa_advanced_config['Freeform']
                        freeform_paths.aaa = str(fabric_freeform_dir / f"{aaa_path}.sh")
                
                # Check for Leaf Freeform Config
                leaf_config = advanced_config.get('Leaf Freeform Config', {})
                if isinstance(leaf_config, dict) and 'Freeform' in leaf_config:
                    leaf_path = leaf_config['Freeform']
                    freeform_paths.leaf = str(fabric_freeform_dir / f"{leaf_path}.sh")
                
                # Check for Spine Freeform Config
                spine_config = advanced_config.get('Spine Freeform Config', {})
                if isinstance(spine_config, dict) and 'Freeform' in spine_config:
                    spine_path = spine_config['Freeform']
                    freeform_paths.spine = str(fabric_freeform_dir / f"{spine_path}.sh")
                
                # Check for Intra-fabric Links Additional Config
                intra_config = advanced_config.get('Intra-fabric Links Additional Config', {})
                if isinstance(intra_config, dict) and 'Freeform' in intra_config:
                    intra_path = intra_config['Freeform']
                    freeform_paths.intra_links = str(fabric_freeform_dir / f"{intra_path}.sh")
            
            # Override with fabric-specific configs if they exist in the FreeForm directory
            if fabric_freeform_dir.exists():
                for config_type, filename in [
                    ("aaa", "AAA Freeform Config.sh"),
                    ("leaf", "Leaf Freeform Config.sh"),
                    ("spine", "Spine Freeform Config.sh"),
                    ("banner", "Banner.sh"),
                    ("intra_links", "Intra-fabric Links Additional Config.sh")
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

    def _determine_fabric_type_from_file(self, fabric_name: str) -> Optional[FabricType]:
        """
        Determine the fabric type by reading the YAML configuration file.
        
        Args:
            fabric_name: Name of the fabric configuration file (without .yaml extension)
            
        Returns:
            FabricType or None if type cannot be determined
        """
        # Get fabric paths from centralized config
        fabric_paths = config_factory.get_fabric_paths()
        
        # Try each possible fabric type configuration path
        possible_paths = [
            (FabricType.VXLAN_EVPN, str(fabric_paths['configs'] / f"{fabric_name}.yaml")),
            (FabricType.MULTI_SITE_DOMAIN, str(fabric_paths['multisite'] / f"{fabric_name}.yaml")),
            (FabricType.INTER_SITE_NETWORK, str(fabric_paths['inter_site'] / f"{fabric_name}.yaml"))
        ]
        
        for fabric_type, config_path in possible_paths:
            if validate_file_exists(config_path):
                fabric_config = load_yaml_file(config_path)
                if fabric_config:
                    config_type = get_nested_value(fabric_config, ('Fabric', 'type'))
                    if config_type:
                        # Map the type string from YAML to FabricType enum
                        fabric_enum = FabricType.from_yaml_type(config_type)
                        if fabric_enum:
                            return fabric_enum
                        else:
                            print(f"⚠️  Unknown fabric type in config: {config_type}")
        
        print(f"❌ Could not determine fabric type for: {fabric_name}")
        return None

# Export the main classes and types
__all__ = [
    'FabricType', 
    'FabricConfig', 
    'FreeformPaths', 
    'FabricBuilder', 
    'PayloadGenerator', 
    'BaseFabricMethods',
    'FabricManager'  # Add the new FabricManager
]

# Import the FabricManager for easy access
from .fabric import FabricManager
