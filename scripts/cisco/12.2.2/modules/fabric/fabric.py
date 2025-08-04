#!/usr/bin/env python3
"""
Fabric Manager - Unified Fabric Management Interface

This module provides a clean, unified interface for all fabric operations with:
- YAML-based fabric configuration management
- Fabric CRUD operations with configuration merging
- Template payload generation with field mapping
- Corp defaults integration
- Freeform configuration support for VXLAN EVPN and ISN fabrics
"""

from typing import Dict, Any, Tuple, Optional
from enum import Enum
from modules.config_utils import (
    load_yaml_file, validate_configuration_files, validate_file_exists,
    merge_configs, apply_field_mapping, flatten_config, 
    get_nested_value, read_freeform_config
)
from config.config_factory import config_factory
import api.fabric as fabric_api

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

class FabricManager:
    """Unified fabric operations manager with YAML configuration support."""
    
    def __init__(self):
        """Initialize with centralized configuration paths."""
        # Get fabric paths from factory
        self.fabric_paths = config_factory.get_fabric_paths()
        
    def _get_fabric_config_path(self, fabric_type: FabricType, fabric_name: str) -> Dict[str, str]:
        """Get configuration paths for a specific fabric type and name."""
        base_configs = {
            FabricType.VXLAN_EVPN: {
                'config_path': str(self.fabric_paths['configs'] / f"{fabric_name}.yaml"),
                'defaults_path': str(self.fabric_paths['defaults'].parent / "cisco_vxlan.yaml"),
                'field_mapping_path': str(self.fabric_paths['field_mapping'].parent / "cisco_vxlan.yaml")
            },
            FabricType.MULTI_SITE_DOMAIN: {
                'config_path': str(self.fabric_paths['multisite'] / f"{fabric_name}.yaml"),
                'defaults_path': str(self.fabric_paths['defaults'].parent / "cisco_multi-site.yaml"),
                'field_mapping_path': str(self.fabric_paths['field_mapping'].parent / "cisco_multi-site.yaml")
            },
            FabricType.INTER_SITE_NETWORK: {
                'config_path': str(self.fabric_paths['inter_site'] / f"{fabric_name}.yaml"),
                'defaults_path': str(self.fabric_paths['defaults'].parent / "cisco_inter-site.yaml"),
                'field_mapping_path': str(self.fabric_paths['field_mapping'].parent / "cisco_inter-site.yaml")
            }
        }
        return base_configs[fabric_type]
    
    def _determine_fabric_type_from_file(self, fabric_name: str) -> Optional[FabricType]:
        """Determine the fabric type by reading the YAML configuration file."""
        # Try each possible fabric type configuration path
        possible_paths = [
            (FabricType.VXLAN_EVPN, str(self.fabric_paths['configs'] / f"{fabric_name}.yaml")),
            (FabricType.MULTI_SITE_DOMAIN, str(self.fabric_paths['multisite'] / f"{fabric_name}.yaml")),
            (FabricType.INTER_SITE_NETWORK, str(self.fabric_paths['inter_site'] / f"{fabric_name}.yaml"))
        ]
        
        for fabric_type, config_path in possible_paths:
            if validate_file_exists(config_path):
                fabric_config = load_yaml_file(config_path)
                if fabric_config and 'Fabric' in fabric_config:
                    yaml_type = get_nested_value(fabric_config, ('Fabric', 'type'))
                    if yaml_type:
                        return FabricType.from_yaml_type(yaml_type)
        
        print(f"[Fabric] Could not determine fabric type for: {fabric_name}")
        return None
    
    def _build_fabric_payload(self, fabric_config: Dict[str, Any], defaults_config: Dict[str, Any], 
                             field_mapping: Dict[str, Any], fabric_name: str, fabric_type: FabricType) -> Dict[str, Any]:
        """Build fabric payload dictionary."""
        # Merge configurations
        final_config = {}
        for key in defaults_config:
            if key in fabric_config:
                final_config[key] = merge_configs(defaults_config[key], fabric_config[key])
            else:
                final_config[key] = defaults_config[key]
        
        # Flatten and apply field mapping
        flat_config = flatten_config(final_config)
        mapped_config = apply_field_mapping(flat_config, flatten_config(field_mapping))
        
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
    
    def _get_freeform_paths(self, fabric_name: str, fabric_type: FabricType, fabric_config: Dict[str, Any]) -> Dict[str, str]:
        """Get freeform configuration file paths for a fabric."""
        freeform_paths = {}
        resources_freeform_dir = self.fabric_paths['freeform']
        
        if fabric_type == FabricType.VXLAN_EVPN:
            # Check for fabric-specific freeform configs first
            fabric_freeform_dir = self.fabric_paths['configs'] / f"{fabric_name}_FreeForm"
            
            # Initialize paths - only banner has default, others are None if not found
            default_paths = {
                'aaa': None,
                'leaf': None,
                'spine': None,
                'banner': str(resources_freeform_dir / "Banner.sh"),  # Only banner has default
                'intra_links': None
            }
            
            # Override with paths from fabric configuration YAML if specified
            if fabric_config:
                # Check Manageability section for AAA config
                manageability_config = fabric_config.get('Manageability', {})
                aaa_config = manageability_config.get('AAA Freeform Config', {})
                if isinstance(aaa_config, dict) and 'Freeform' in aaa_config:
                    default_paths['aaa'] = aaa_config['Freeform']
                
                # Check Advanced section
                advanced_config = fabric_config.get('Advanced', {})
                
                # Check for AAA Freeform Config in Advanced (fallback)
                if aaa_config := advanced_config.get('AAA Freeform Config', {}):
                    if isinstance(aaa_config, dict) and 'Freeform' in aaa_config:
                        default_paths['aaa'] = aaa_config['Freeform']
                
                # Check for other freeform configs
                for config_key, path_key in [
                    ('Leaf Freeform Config', 'leaf'),
                    ('Spine Freeform Config', 'spine'),
                    ('Intra-fabric Links Additional Config', 'intra_links')
                ]:
                    config = advanced_config.get(config_key, {})
                    if isinstance(config, dict) and 'Freeform' in config:
                        default_paths[path_key] = config['Freeform']
            
            # Override with fabric-specific configs if they exist
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
                        default_paths[config_type] = str(fabric_specific_path)
            
            freeform_paths = default_paths
            
        elif fabric_type == FabricType.INTER_SITE_NETWORK:
            # Load from defaults configuration
            defaults_path = self._get_fabric_config_path(fabric_type, fabric_name)['defaults_path']
            defaults_config = load_yaml_file(defaults_path)
            
            if defaults_config:
                advanced_config = defaults_config.get('Advanced', {})
                
                fabric_freeform = advanced_config.get('Fabric Freeform', {}).get('freeform')
                if fabric_freeform:
                    freeform_paths['fabric'] = fabric_freeform
                
                aaa_freeform = advanced_config.get('AAA Freeform Config', {}).get('freeform')
                if aaa_freeform:
                    freeform_paths['aaa'] = aaa_freeform
        
        return freeform_paths
    
    def _add_freeform_content_to_payload(self, payload_data: Dict[str, Any], fabric_type: FabricType, 
                                       freeform_paths: Dict[str, str]) -> None:
        """Add freeform configuration content to the API payload."""
        if fabric_type == FabricType.VXLAN_EVPN:
            # AAA Freeform Config
            aaa_path = freeform_paths.get('aaa')
            if aaa_path and validate_file_exists(aaa_path):
                payload_data["AAA_SERVER_CONF"] = read_freeform_config(aaa_path)
            elif aaa_path:
                print(f"[Fabric] AAA freeform config file not found: {aaa_path}")
            
            # Leaf Freeform Config
            leaf_path = freeform_paths.get('leaf')
            if leaf_path and validate_file_exists(leaf_path):
                payload_data["EXTRA_CONF_LEAF"] = read_freeform_config(leaf_path)
            elif leaf_path:
                print(f"[Fabric] Leaf freeform config file not found: {leaf_path}")
            
            # Spine Freeform Config
            spine_path = freeform_paths.get('spine')
            if spine_path and validate_file_exists(spine_path):
                payload_data["EXTRA_CONF_SPINE"] = read_freeform_config(spine_path)
            elif spine_path:
                print(f"[Fabric] Spine freeform config file not found: {spine_path}")
            
            # Intra-fabric Links Additional Config
            intra_links_path = freeform_paths.get('intra_links')
            if intra_links_path and validate_file_exists(intra_links_path):
                payload_data["INTRA_FABRIC_LINK_FREEFORM"] = read_freeform_config(intra_links_path)
            elif intra_links_path:
                print(f"[Fabric] Intra-fabric links freeform config file not found: {intra_links_path}")
                
            # Banner config (always has default)
            banner_path = freeform_paths.get('banner')
            if banner_path and validate_file_exists(banner_path):
                banner_data = '`' + read_freeform_config(banner_path) + '`'
                payload_data["BANNER"] = banner_data
            else:
                print(f"[Fabric] Banner config file not found: {banner_path}")

        elif fabric_type == FabricType.INTER_SITE_NETWORK:
            # Fabric Freeform Config
            fabric_path = freeform_paths.get('fabric')
            if fabric_path and validate_file_exists(fabric_path):
                payload_data["FABRIC_FREEFORM"] = read_freeform_config(fabric_path)
            elif fabric_path:
                print(f"[Fabric] Fabric freeform config file not found: {fabric_path}")
                
            # AAA Freeform Config
            aaa_path = freeform_paths.get('aaa')
            if aaa_path and validate_file_exists(aaa_path):
                payload_data["AAA_FREEFORM"] = read_freeform_config(aaa_path)
            elif aaa_path:
                print(f"[Fabric] AAA freeform config file not found: {aaa_path}")
    
    def _build_complete_payload(self, fabric_name: str) -> Tuple[Dict[str, Any], str, str]:
        """Build complete fabric payload for API operations."""
        # Determine fabric type
        fabric_type = self._determine_fabric_type_from_file(fabric_name)
        if not fabric_type:
            raise ValueError(f"Could not determine fabric type for '{fabric_name}'")
        
        # Get configuration paths
        config_paths = self._get_fabric_config_path(fabric_type, fabric_name)
        
        # Validate required files for VXLAN EVPN
        if fabric_type == FabricType.VXLAN_EVPN:
            required_files = [
                config_paths['config_path'], 
                config_paths['defaults_path'], 
                config_paths['field_mapping_path']
            ]
            files_exist, missing_files = validate_configuration_files(required_files)
            if not files_exist:
                raise ValueError(f"Missing required configuration files: {missing_files}")
        
        # Load configurations
        fabric_config = load_yaml_file(config_paths['config_path'])
        defaults_config = load_yaml_file(config_paths['defaults_path'])
        field_mapping = load_yaml_file(config_paths['field_mapping_path'])
        
        if not all([fabric_config, defaults_config, field_mapping]):
            raise ValueError("Could not load required configurations or mappings")
        
        # Build payload
        payload_data = self._build_fabric_payload(
            fabric_config, defaults_config, field_mapping, fabric_name, fabric_type
        )
        
        # Add freeform content for supported fabric types
        if fabric_type in [FabricType.VXLAN_EVPN, FabricType.INTER_SITE_NETWORK]:
            freeform_paths = self._get_freeform_paths(fabric_name, fabric_type, fabric_config)
            
            # Log the freeform config paths being used
            if freeform_paths:
                print("[Fabric] Using freeform config files:")
                for config_type, path in freeform_paths.items():
                    if path:
                        print(f"  {config_type.title()}: {path}")
            
            self._add_freeform_content_to_payload(payload_data, fabric_type, freeform_paths)
        
        # Get template name from fabric type
        template_name = fabric_type.value
        
        return payload_data, template_name, fabric_name
    
    # --- Fabric CRUD Operations ---
    
    def create_fabric(self, fabric_name: str) -> bool:
        """Create a fabric using YAML configuration."""
        print(f"[Fabric] Creating fabric '{fabric_name}'")
        
        try:
            payload_data, template_name, fabric_name_resolved = self._build_complete_payload(fabric_name)
            print(f"[Fabric] Using config file: {self._get_fabric_config_path(self._determine_fabric_type_from_file(fabric_name), fabric_name)['config_path']}")
            
            return fabric_api.create_fabric(
                fabric_name=fabric_name_resolved,
                template_name=template_name,
                payload_data=payload_data
            )
        except Exception as e:
            print(f"[Fabric] Error creating fabric '{fabric_name}': {e}")
            return False
    
    def update_fabric(self, fabric_name: str) -> bool:
        """Update a fabric using YAML configuration."""
        print(f"[Fabric] Updating fabric '{fabric_name}'")
        
        try:
            payload_data, template_name, fabric_name_resolved = self._build_complete_payload(fabric_name)
            print(f"[Fabric] Using config file: {self._get_fabric_config_path(self._determine_fabric_type_from_file(fabric_name), fabric_name)['config_path']}")
            
            return fabric_api.update_fabric(
                fabric_name=fabric_name_resolved,
                template_name=template_name,
                payload_data=payload_data
            )
        except Exception as e:
            print(f"[Fabric] Error updating fabric '{fabric_name}': {e}")
            return False
    
    def delete_fabric(self, fabric_name: str) -> bool:
        """Delete a fabric."""
        print(f"[Fabric] Deleting fabric '{fabric_name}'")
        return fabric_api.delete_fabric(fabric_name)
    
    # --- Configuration Operations ---
    
    def recalculate_config(self, fabric_name: str) -> bool:
        """Recalculate fabric configuration."""
        print(f"[Fabric] Recalculating configuration for fabric '{fabric_name}'")
        return fabric_api.recalculate_config(fabric_name)
    
    def get_pending_config(self, fabric_name: str) -> Optional[Dict[str, Any]]:
        """Get pending configuration with formatted output."""
        print(f"[Fabric] Getting pending configuration for fabric '{fabric_name}'")
        return fabric_api.get_pending_config(fabric_name)

    def deploy_fabric(self, fabric_name: str) -> bool:
        """Deploy fabric configuration."""
        print(f"[Fabric] Deploying configuration for fabric '{fabric_name}'")
        return fabric_api.deploy_fabric_config(fabric_name)
    
    # --- Multi-Site Domain Operations ---
    
    def add_to_msd(self, parent_fabric: str, child_fabric: str) -> bool:
        """Add a child fabric to a Multi-Site Domain."""
        print(f"[Fabric] Adding fabric '{child_fabric}' to MSD '{parent_fabric}'")
        return fabric_api.add_MSD(parent_fabric, child_fabric)
    
    def remove_from_msd(self, parent_fabric: str, child_fabric: str, force: bool = False) -> bool:
        """Remove a child fabric from a Multi-Site Domain."""
        print(f"[Fabric] Removing fabric '{child_fabric}' from MSD '{parent_fabric}'")
        return fabric_api.remove_MSD(parent_fabric, child_fabric)