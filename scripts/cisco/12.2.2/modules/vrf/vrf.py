#!/usr/bin/env python3
"""
VRF Manager - Unified VRF Management Interface

This module provides a clean, unified interface for all VRF operations with:
- YAML-based VRF configuration management
- VRF CRUD operations with configuration merging
- Template payload generation with field mapping
- Corp defaults integration
- VRF attachment/detachment to switch interfaces
"""

from typing import List, Dict, Any, Tuple, Optional
from modules.config_utils import load_yaml_file, validate_configuration_files, merge_configs, apply_field_mapping, flatten_config
from config.config_factory import config_factory
import api.vrf as vrf_api

class VRFManager:
    """Unified VRF operations manager with YAML configuration support."""
    
    def __init__(self):
        """Initialize with centralized configuration paths."""
        # Get configuration paths from factory
        config_paths = config_factory.create_vrf_config()
        self.switch_config_paths = config_factory.create_switch_config()
        
        # Set up configuration file paths
        self.config_path = config_paths.config_path
        self.defaults_path = config_paths.defaults_path
        self.field_mapping_path = config_paths.field_mapping_path
        
        # Lazy-loaded cached configurations
        self._defaults = None
        self._field_mapping = None
        self._vrfs = None
    
    @property
    def defaults(self) -> Dict[str, Any]:
        """Get corp defaults with lazy loading."""
        if self._defaults is None:
            self._defaults = load_yaml_file(str(self.defaults_path))
        return self._defaults
    
    @property
    def field_mapping(self) -> Dict[str, Any]:
        """Get field mapping with lazy loading."""
        if self._field_mapping is None:
            self._field_mapping = load_yaml_file(str(self.field_mapping_path))
        return self._field_mapping
    
    @property
    def vrfs(self) -> List[Dict[str, Any]]:
        """Get VRF configurations with lazy loading and caching."""
        if self._vrfs is None:
            self._load_vrfs()
        return self._vrfs
    
    def _load_vrfs(self) -> None:
        """Load VRF configurations from YAML file."""
        try:
            print(f"[VRF] Loading VRF config from: {self.config_path}")
            config_data = load_yaml_file(str(self.config_path))
            self._vrfs = config_data.get('VRF', [])
        except Exception as e:
            print(f"Error loading VRF configuration: {e}")
            self._vrfs = []
    
    def _get_vrf(self, vrf_name: str) -> Optional[Dict[str, Any]]:
        """Find VRF by name regardless of fabric."""
        return next(
            (vrf for vrf in self.vrfs 
             if vrf.get('VRF Name') == vrf_name),
            None
        )
    
    def _validate_resources(self) -> None:
        """Validate required resource files exist."""
        validate_configuration_files([str(self.defaults_path), str(self.field_mapping_path)])
    
    def _build_vrf_template_config(self, vrf_name: str, vrf: Dict[str, Any]) -> Dict[str, Any]:
        """Build VRF template configuration dictionary."""
        # Extract required fields from VRF data
        vrf_id = str(vrf.get('VRF ID', 0))
        vlan_id = str(vrf.get('VLAN ID', 0))
        general_params = vrf.get('General Parameters', {})
        
        # Build base template config
        template_config = {
            "vrfName": vrf_name,
            "vrfSegmentId": vrf_id,
            "vrfVlanId": vlan_id,
            "vrfDescription": general_params.get("VRF Description", vrf_name),
            "vrfVlanName": general_params.get("VRF VLAN Name", vrf_name),
            "vrfIntfDescription": general_params.get("VRF Interface Description", vrf_name),
        }
        
        # Apply corp defaults with field mapping
        self._apply_template_defaults(template_config, vrf)
        
        return template_config
    
    def _apply_template_defaults(self, template_config: Dict[str, Any], vrf: Dict[str, Any]) -> None:
        """Apply corp defaults with field mapping to template config."""
        # Merge VRF config with defaults
        final_config = {}
        for key in self.defaults:
            if key in vrf:
                final_config[key] = merge_configs(self.defaults[key], vrf[key])
            else:
                final_config[key] = self.defaults[key]
        
        # Flatten and apply field mapping
        flat_config = flatten_config(final_config)
        mapped_config = apply_field_mapping(flat_config, flatten_config(self.field_mapping))
        
        # Update template config with mapped values
        for key, value in mapped_config.items():
            if value:  # Only add non-empty values
                template_config[key] = value
    
    def _build_vrf_payload(self, fabric_name: str, vrf_name: str, vrf: Dict[str, Any]) -> Dict[str, Any]:
        """Build VRF payload dictionary."""
        # Extract required fields from VRF data
        vrf_id = vrf.get('VRF ID', 0)
        vlan_id = vrf.get('VLAN ID', 0)
        general_params = vrf.get('General Parameters', {})
        
        # Build base payload
        payload = {
            "fabric": fabric_name,
            "vrfName": vrf_name,
            "vrfTemplate": self.defaults.get("vrfTemplate", "Default_VRF_Universal"),
            "vrfExtensionTemplate": self.defaults.get("vrfExtensionTemplate", "Default_VRF_Extension_Universal"),
            "vrfId": str(vrf_id),
            "vrfVlanId": str(vlan_id),
            "vrfDescription": general_params.get("VRF Description", vrf_name),
            # Additional fields for complete payload
            "tenantName": None,
            "serviceVrfTemplate": None,
            "source": None,
            "tag": None
        }
        
        return payload

    def _build_complete_payload(self, fabric_name: str, vrf_name: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Build complete VRF payload for API operations."""
        self._validate_resources()
        
        vrf = self._get_vrf(vrf_name)
        if not vrf:
            raise ValueError(f"VRF '{vrf_name}' not found in configuration")
        
        # Build VRF payload using dictionary approach
        payload = self._build_vrf_payload(fabric_name, vrf_name, vrf)
        
        # Build template config using dictionary approach
        template_config = self._build_vrf_template_config(vrf_name, vrf)

        # Return both payload and template config as dictionaries
        # The API layer will handle JSON encoding
        return payload, template_config
    
    # --- VRF CRUD Operations ---
    
    def create_vrf(self, fabric_name: str, vrf_name: str) -> bool:
        """Create a VRF using YAML configuration."""
        print(f"[VRF] Creating VRF '{vrf_name}' in fabric '{fabric_name}'")
        payload, template_config = self._build_complete_payload(fabric_name, vrf_name)
        return vrf_api.create_vrf(fabric_name, payload, template_config)
    
    def update_vrf(self, fabric_name: str, vrf_name: str) -> bool:
        """Update a VRF using YAML configuration."""
        print(f"[VRF] Updating VRF '{vrf_name}' in fabric '{fabric_name}'")
        payload, template_config = self._build_complete_payload(fabric_name, vrf_name)
        return vrf_api.update_vrf(fabric_name, vrf_name, payload, template_config)
    
    def delete_vrf(self, fabric_name: str, vrf_name: str) -> bool:
        """Delete a VRF."""
        print(f"[VRF] Deleting VRF '{vrf_name}' in fabric '{fabric_name}'")
        return vrf_api.delete_vrf(fabric_name, vrf_name)
    
    # --- VRF Attachment Operations ---
    
    def attach_vrf(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Attach VRF to switch interfaces based on YAML configuration."""
        print(f"[VRF] Attaching VRF to switch '{switch_name}' ({role}) in fabric '{fabric_name}'")
        
        try:
            # Load and validate switch configuration
            switch_path = self.switch_config_paths['configs_dir'] / fabric_name / role / f"{switch_name}.yaml"
            print(f"[VRF] Loading switch config from: {switch_path}")
            
            if not switch_path.exists():
                print(f"[VRF] Switch configuration not found: {switch_path}")
                return False
            
            switch_config = load_yaml_file(str(switch_path))
            if not switch_config:
                print(f"[VRF] Failed to load switch configuration: {switch_path}")
                return False
            
            serial_number = switch_config.get('Serial Number', '')
            if not serial_number:
                print(f"[VRF] No serial number found in switch configuration: {switch_name}")
                return False
            
            # Find VRF from routed interfaces
            vrf_name = self._find_vrf_in_switch(switch_config, switch_name)
            if not vrf_name:
                return False
            
            # Get VRF details
            vrf_details = self._get_vrf(vrf_name)
            if not vrf_details:
                print(f"[VRF] No VRF found with name '{vrf_name}'")
                return False
            
            vlan_id = vrf_details.get("VLAN ID")
            if not vlan_id:
                print(f"[VRF] No VLAN ID found for VRF '{vrf_name}'")
                return False
            
            # Build and execute VRF attachment
            payload = self._build_attachment_payload(vrf_name, vlan_id, switch_name, serial_number, fabric_name, True)
            return vrf_api.update_vrf_attachment(fabric_name, payload)
            
        except Exception as e:
            print(f"[VRF] Error attaching VRF: {e}")
            return False
    
    def detach_vrf(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Detach VRF from switch interfaces based on YAML configuration."""
        print(f"[VRF] Detaching VRF from switch '{switch_name}' ({role}) in fabric '{fabric_name}'")
        
        try:
            # Load and validate switch configuration
            switch_path = self.switch_config_paths['configs_dir'] / fabric_name / role / f"{switch_name}.yaml"
            print(f"[VRF] Loading switch config from: {switch_path}")
            
            if not switch_path.exists():
                print(f"[VRF] Switch configuration not found: {switch_path}")
                return False
            
            switch_config = load_yaml_file(str(switch_path))
            if not switch_config:
                print(f"[VRF] Failed to load switch configuration: {switch_path}")
                return False
            
            serial_number = switch_config.get('Serial Number', '')
            if not serial_number:
                print(f"[VRF] No serial number found in switch configuration: {switch_name}")
                return False
            
            # Find VRF from routed interfaces
            vrf_name = self._find_vrf_in_switch(switch_config, switch_name)
            if not vrf_name:
                return False
            
            # Get VRF details
            vrf_details = self._get_vrf(vrf_name)
            if not vrf_details:
                print(f"[VRF] No VRF found with name '{vrf_name}'")
                return False
            
            vlan_id = vrf_details.get("VLAN ID")
            if not vlan_id:
                print(f"[VRF] No VLAN ID found for VRF '{vrf_name}'")
                return False
            
            # Build and execute VRF detachment
            payload = self._build_attachment_payload(vrf_name, vlan_id, switch_name, serial_number, fabric_name, False)
            return vrf_api.update_vrf_attachment(fabric_name, payload)
            
        except Exception as e:
            print(f"[VRF] Error detaching VRF: {e}")
            return False
    
    def _find_vrf_in_switch(self, switch_config: Dict[str, Any], switch_name: str) -> Optional[str]:
        """Find VRF name from switch interface configuration with int_routed_host policy."""
        interfaces = switch_config.get("Interface", [])
        
        if not isinstance(interfaces, list):
            print(f"[VRF] Invalid interface format in switch '{switch_name}'")
            return None
        
        for interface_item in interfaces:
            if not isinstance(interface_item, dict):
                continue
                
            # Each interface item is a dict with one key (interface name)
            for interface_name, interface_config in interface_item.items():
                if not isinstance(interface_config, dict):
                    continue
                    
                if (interface_config.get("policy") == "int_routed_host" and 
                    interface_config.get("Interface VRF")):
                    vrf_name = interface_config.get("Interface VRF")
                    print(f"[VRF] Found routed interface {interface_name} using VRF '{vrf_name}'")
                    return vrf_name

        print(f"[VRF] No routed interfaces with VRF configuration found in switch '{switch_name}'")
        return None
    
    def _build_attachment_payload(self, vrf_name: str, vlan_id: int, switch_name: str, serial_number: str, fabric_name: str, deployment: bool = True) -> List[Dict[str, Any]]:
        """Build the VRF attachment/detachment payload for the API."""
        attachment_list = []
        
        # Build the main VRF attachment object
        vrf_attachment = {
            "vrfName": vrf_name,
            "lanAttachList": [{
                "fabric": fabric_name,
                "vrfName": vrf_name,
                "serialNumber": serial_number,
                "vlan": str(vlan_id),
                "deployment": deployment,
                "instanceValues": "",
                "freeformConfig": ""
            }]
        }
        
        # Return as array (API expects ArrayList)
        attachment_list.append(vrf_attachment)
        return attachment_list