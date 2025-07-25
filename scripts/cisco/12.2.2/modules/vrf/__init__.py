#!/usr/bin/env python3
"""
VRF Management Module - Core Components

This module provides the core functionality for building and managing VRFs:
- VRF Creation, Update, and Deletion
- VRF Template Configuration Management
- VRF Attachment Management

It handles configuration merging, field mapping, and API payload generation
for Cisco NDFC VRF management.
"""

import os
import sys
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Update import path to go back to parent directory for api and modules
sys.path.append(str(Path(__file__).parent.parent.absolute()))
import api.vrf as vrf_api
from modules.config_utils import (
    load_yaml_file, merge_configs, 
    apply_field_mapping, get_nested_value,
    validate_file_exists, 
    validate_configuration_files, flatten_config
)

# --- Constants and Enums ---

class VRFTemplate(Enum):
    """Enumeration of supported VRF templates."""
    DEFAULT_VRF_UNIVERSAL = "Default_VRF_Universal"
    DEFAULT_VRF_EXTENSION_UNIVERSAL = "Default_VRF_Extension_Universal"

@dataclass
class VRFConfig:
    """Configuration paths and parameters for VRF building."""
    config_path: str
    defaults_path: str
    field_mapping_path: str

@dataclass
class VRFAttachmentConfig:
    """Configuration for VRF attachments."""
    fabric: str
    vrf_name: str
    attach_list: List[Dict[str, Any]]

# --- Utility Classes ---

class VRFBuilder:
    """Main class for building and managing VRFs."""
    
    def __init__(self):
        """Initialize the VRFBuilder with project paths."""
        # Adjust path calculation for modules subdirectory
        self.script_dir = Path(__file__).parent.parent.parent.absolute()
        self.project_root = self.script_dir.parents[2]
        self.resources_dir = self.script_dir / "resources"
        self.vrf_configs_dir = self.project_root / "network_configs" / "5_segment"
    
    def get_vrf_config(self) -> VRFConfig:
        """Get configuration paths for VRF management."""
        return VRFConfig(
            config_path=str(self.vrf_configs_dir / "vrf.yaml"),
            defaults_path=str(self.resources_dir / "corp_defaults" / "vrf.yaml"),
            field_mapping_path=str(self.resources_dir / "_field_mapping" / "vrf.yaml")
        )
    
    def get_fabric_vrfs(self, fabric_name: str) -> List[Dict[str, Any]]:
        """Get all VRFs for a specific fabric."""
        config = self.get_vrf_config()
        vrf_config_list = load_yaml_file(config.config_path)
        
        if not vrf_config_list:
            return []
        
        fabric_vrfs = []
        if isinstance(vrf_config_list, dict) and "VRF" in vrf_config_list:
            vrf_list = vrf_config_list["VRF"]
            for vrf in vrf_list:
                if vrf.get("Fabric") == fabric_name:
                    fabric_vrfs.append(vrf)
        
        return fabric_vrfs
    
    def get_all_fabrics(self) -> List[str]:
        """Get a list of all unique fabric names from VRF configurations."""
        config = self.get_vrf_config()
        vrf_config_list = load_yaml_file(config.config_path)
        
        if not vrf_config_list:
            return []
        
        fabrics = set()
        if isinstance(vrf_config_list, dict) and "VRF" in vrf_config_list:
            vrf_list = vrf_config_list["VRF"]
            for vrf in vrf_list:
                fabric = vrf.get("Fabric")
                if fabric:
                    fabrics.add(fabric)
        
        return sorted(list(fabrics))

class VRFPayloadGenerator:
    """Handles the generation of API payloads for VRF operations."""
    
    @staticmethod
    def prepare_vrf_payload(config: VRFConfig, vrf_name: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[str]]:
        """Prepare the API payload for creating/updating a VRF.
        
        Returns:
            Tuple of (main_payload, template_payload, fabric_name)
        """
        
        # Load configurations
        vrf_config_list = load_yaml_file(config.config_path)
        defaults_config = load_yaml_file(config.defaults_path)
        field_mapping = load_yaml_file(config.field_mapping_path)

        if not all([vrf_config_list, defaults_config, field_mapping]):
            print("Could not load required VRF configurations or mappings. Exiting.")
            return None, None, None

        # Find the specific VRF in the list
        vrf_config = None
        if isinstance(vrf_config_list, dict) and "VRF" in vrf_config_list:
            vrf_list = vrf_config_list["VRF"]
            for vrf in vrf_list:
                if vrf.get("VRF Name") == vrf_name:
                    vrf_config = vrf
                    break
        
        if not vrf_config:
            print(f"VRF '{vrf_name}' not found in configuration file.")
            return None, None, None

        # Extract fabric name from the VRF configuration
        fabric_name = vrf_config.get("Fabric")
        if not fabric_name:
            print(f"No fabric specified for VRF '{vrf_name}' in configuration.")
            return None, None, None

        # Merge configurations
        final_config = VRFPayloadGenerator._merge_all_configs(defaults_config, vrf_config)
        
        # Flatten and map configurations
        flat_config = flatten_config(final_config)
        mapped_config = apply_field_mapping(flat_config, flatten_config(field_mapping))

        # Build main VRF payload
        main_payload = VRFPayloadGenerator._build_main_payload(mapped_config, vrf_config, fabric_name)
        
        # Build template config payload from YAML configurations
        template_payload = VRFPayloadGenerator._build_template_payload(mapped_config, vrf_config)
        
        return main_payload, template_payload, fabric_name

    @staticmethod
    def _merge_all_configs(defaults_config: Dict[str, Any], vrf_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge default and VRF configurations."""
        final_config = {}
        for key in defaults_config:
            if key in vrf_config:
                final_config[key] = merge_configs(defaults_config[key], vrf_config[key])
            else:
                final_config[key] = defaults_config[key]
        return final_config

    @staticmethod
    def _build_main_payload(mapped_config: Dict[str, Any], vrf_config: Dict[str, Any], fabric_name: str) -> Dict[str, Any]:
        """Build the main VRF API payload."""
        vrf_name = vrf_config.get("VRF Name")
        vrf_id = vrf_config.get("VRF ID", "")
        vlan_id = vrf_config.get("VLAN ID", "")
        
        payload = {
            "fabric": fabric_name,
            "vrfName": vrf_name,
            "vrfTemplate": VRFTemplate.DEFAULT_VRF_UNIVERSAL.value,
            "vrfExtensionTemplate": VRFTemplate.DEFAULT_VRF_EXTENSION_UNIVERSAL.value,
            "vrfId": str(vrf_id),
            "vrfVlanId": str(vlan_id),
        }
        print(payload)
        
        # Add description fields from General Parameters or use VRF name as default
        general_params = vrf_config.get("General Parameters", {})
        payload["vrfDescription"] = general_params.get("VRF Description", vrf_name)
        
        # Add optional fields if they exist in mapped config
        optional_fields = ["tenantName", "serviceVrfTemplate", "source", "tag"]
        for field in optional_fields:
            if field in mapped_config:
                payload[field] = mapped_config[field]
        
        return payload

    @staticmethod
    def _build_template_payload(mapped_config: Dict[str, Any], vrf_config: Dict[str, Any]) -> Dict[str, Any]:
        """Build the VRF template configuration payload from YAML configurations."""
        # Get values from the specific VRF config
        vrf_name = vrf_config.get("VRF Name")
        vrf_id = vrf_config.get("VRF ID", "")
        vlan_id = vrf_config.get("VLAN ID", "")
        general_params = vrf_config.get("General Parameters", {})
        route_target = vrf_config.get("Route Target", {})
        
        # Build template payload from YAML configurations
        template_payload = {
            "vrfName": vrf_name,
            "vrfSegmentId": str(vrf_id),
            "vrfVlanId": str(vlan_id),
            "vrfDescription": general_params.get("VRF Description", vrf_name),
            "vrfVlanName": general_params.get("VRF VLAN Name", vrf_name),
            "vrfIntfDescription": general_params.get("VRF Interface Description", vrf_name),
        }
        
        # Add route target information
        if route_target.get("Import"):
            template_payload["routeTargetImport"] = route_target["Import"]
        if route_target.get("Export"):
            template_payload["routeTargetExport"] = route_target["Export"]
        
        # Override with any mapped configuration values
        for key, value in mapped_config.items():
            if value:  # Only add non-empty values
                template_payload[key] = value
        
        return template_payload

class BaseVRFMethods:
    """Base class with shared methods for VRF operations."""
    
    def __init__(self):
        self.builder = VRFBuilder()
        self.payload_generator = VRFPayloadGenerator()

# Export the main classes and types
__all__ = [
    'VRFTemplate', 
    'VRFConfig', 
    'VRFAttachmentConfig',
    'VRFBuilder', 
    'VRFPayloadGenerator', 
    'BaseVRFMethods'
]
