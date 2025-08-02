#!/usr/bin/env python3
"""
VRF Builder - Attach/Detach Operations

This module handles VRF attachment and detachment operations:
- Attaching VRFs to switches based on VLAN matching
- Detaching VRFs from switches based on VLAN matching
- Switch discovery and payload building
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import api.vrf as vrf_api
from modules.config_utils import load_yaml_file
from . import VRFBuilder, VRFPayloadGenerator

class VRFAttachment:
    """Handles VRF attachment and detachment operations."""
    
    def __init__(self):
        self.builder = VRFBuilder()
        self.payload_generator = VRFPayloadGenerator()
    
    def manage_vrf_by_switch(self, fabric_name: str, switch_role: str, switch_name: str, operation: str = "attach") -> bool:
        """
        Attach or detach VRF to/from a specific switch based on fabric, role, and switch name.
        
        Args:
            fabric_name: Name of the fabric
            switch_role: Role of the switch (leaf, spine, border_gateway)
            switch_name: Name of the switch
            operation: "attach" or "detach"
            
        Returns:
            bool: True if successful, False otherwise
        """
        vrf_name = None  # Initialize to avoid UnboundLocalError
        try:
            # Load switch configuration and find VRF
            switch_config, serial_number = self._load_switch_config(fabric_name, switch_role, switch_name)
            if not switch_config:
                return False
            
            vrf_name = self._find_vrf_in_switch(switch_config, switch_name)
            if not vrf_name:
                return False
            
            print(f"  - VRF '{vrf_name}' configured on {switch_name} ({serial_number})")
            
            # Get VRF details and build payload
            vrf_details = self._find_vrf_by_name(vrf_name, fabric_name)
            if not vrf_details:
                print(f"No VRF found with name '{vrf_name}' in fabric '{fabric_name}'")
                return False
            
            vlan_id = vrf_details.get("VLAN ID")
            switch_info = [{
                'hostname': switch_name,
                'serial_number': serial_number,
                'ip_address': switch_config.get('IP Address', ''),
                'role': switch_role,
                'vrf_name': vrf_name
            }]
            
            # Execute VRF operation
            deployment = operation == "attach"
            payload = self._build_vrf_payload(vrf_name, vlan_id, switch_info, fabric_name, deployment)
            
            success = (vrf_api.attach_vrf_to_switches(fabric_name, vrf_name, payload) if operation == "attach" 
                      else vrf_api.detach_vrf_from_switches(fabric_name, vrf_name, payload))
            return success
                
        except Exception as e:
            vrf_display = vrf_name if vrf_name else "unknown VRF"
            print(f"Error {operation}ing {vrf_display} on switch {switch_name}: {e}")
            return False

    def _find_vrf_by_name(self, vrf_name: str, fabric_name: str) -> Optional[Dict[str, Any]]:
        """Find VRF details by VRF name and fabric name."""
        config = self.builder.get_vrf_config()
        vrf_config_list = load_yaml_file(config.config_path)
        
        if isinstance(vrf_config_list, dict) and "VRF" in vrf_config_list:
            vrf_list = vrf_config_list["VRF"]
            for vrf in vrf_list:
                if (vrf.get("Fabric") == fabric_name and 
                    vrf.get("VRF Name") == vrf_name):
                    return vrf
        return None

    def _build_vrf_payload(self, vrf_name: str, vlan_id: int, switches: List[Dict[str, Any]], fabric_name: str, deployment: bool = True) -> List[Dict[str, Any]]:
        """Build the VRF attachment/detachment payload for the switches.
        
        Args:
            vrf_name: Name of the VRF
            vlan_id: VLAN ID
            switches: List of switches to attach/detach
            fabric_name: Name of the fabric
            deployment: True for attach, False for detach
            
        Returns:
            List of VRF attachment objects (array format expected by API).
        """
        attachment_list = []
        
        # Build the main VRF attachment object
        vrf_attachment = {
            "vrfName": vrf_name,
            "lanAttachList": []
        }
        
        # Add each switch to the lanAttachList
        for switch in switches:
            attach_item = {
                "fabric": fabric_name,
                "vrfName": vrf_name,
                "serialNumber": switch['serial_number'],
                "vlan": str(vlan_id),
                "deployment": deployment,
                "instanceValues": "",
                "freeformConfig": ""
            }
            vrf_attachment["lanAttachList"].append(attach_item)
        
        # Return as array (API expects ArrayList)
        attachment_list.append(vrf_attachment)
        return attachment_list

    def _load_switch_config(self, fabric_name: str, switch_role: str, switch_name: str) -> tuple:
        """Load switch configuration and return config and serial number."""
        from config.config_factory import config_factory
        switch_paths = config_factory.create_switch_config()
        switch_path = switch_paths['configs_dir'] / fabric_name / switch_role / f"{switch_name}.yaml"
        
        if not switch_path.exists():
            print(f"Switch configuration not found: {switch_path}")
            return None, None
        
        switch_config = load_yaml_file(str(switch_path))
        if not switch_config:
            print(f"Failed to load switch configuration: {switch_path}")
            return None, None
        
        serial_number = switch_config.get('Serial Number', '')
        if not serial_number:
            print(f"No serial number found in switch configuration: {switch_name}")
            return None, None
        
        return switch_config, serial_number

    def _find_vrf_in_switch(self, switch_config: Dict[str, Any], switch_name: str) -> Optional[str]:
        """Find VRF name from switch interface configuration with int_routed_host policy."""
        interfaces = switch_config.get("Interface", [])
        
        if not isinstance(interfaces, list):
            print(f"Invalid interface format in switch '{switch_name}'")
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
                    print(f"  - Found routed interface {interface_name} using VRF '{vrf_name}'")
                    return vrf_name
        
        print(f"No routed interfaces with VRF configuration found in switch '{switch_name}'")
        return None