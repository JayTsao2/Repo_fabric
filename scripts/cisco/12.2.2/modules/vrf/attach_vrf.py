#!/usr/bin/env python3
"""
VRF Builder - Attach/Detach Operations

This module handles VRF attachment and detachment operations:
- Attaching VRFs to switches based on VLAN matching
- Detaching VRFs from switches based on VLAN matching
- Switch discovery and payload building
"""

from typing import Dict, Any, List, Optional
from modules.common_utils import setup_module_path, MessageFormatter, create_main_function_wrapper
setup_module_path(__file__)

import api.vrf as vrf_api
from modules.config_utils import load_yaml_file
from . import BaseVRFMethods

class VRFAttachment(BaseVRFMethods):
    """Handles VRF attachment and detachment operations."""
    
    def manage_vrf_by_name(self, vrf_name: str, fabric_name: str, operation: str = "attach") -> bool:
        """
        Attach or detach VRF to/from switches based on VRF name match in switch interface configurations.
        
        Args:
            vrf_name: VRF name to match in switch interface configurations
            fabric_name: Name of the fabric to search for switches
            operation: "attach" or "detach"
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            action = "Attaching" if operation == "attach" else "Detaching"
            preposition = "to" if operation == "attach" else "from"
            print(f"\n=== {action} VRF '{vrf_name}' {preposition} switches in Fabric: {fabric_name} ===")
            
            # Step 1: Get VRF details from configuration
            vrf_details = self._find_vrf_by_name(vrf_name, fabric_name)
            if not vrf_details:
                print(f"❌ No VRF found with name '{vrf_name}' in fabric '{fabric_name}'")
                return False
            
            vlan_id = vrf_details.get("VLAN ID")
            print(f"📋 Found VRF: {vrf_name} with VLAN ID: {vlan_id}")
            
            # Step 2: Find switches with matching VRF interface configuration
            matching_switches = self._find_switches_with_vrf_interface(vrf_name, fabric_name)
            if not matching_switches:
                print(f"❌ No switches found with VRF '{vrf_name}' interface configuration in fabric '{fabric_name}'")
                return False
            
            print(f"📋 Found {len(matching_switches)} switches with VRF '{vrf_name}' interface:")
            for switch in matching_switches:
                print(f"  - {switch['hostname']} ({switch['serial_number']}) - Role: {switch['role']}")
            
            # Step 3: Build payload
            deployment = operation == "attach"
            payload = self._build_vrf_payload(vrf_name, vlan_id, matching_switches, fabric_name, deployment)
            
            # Step 4: Execute operation
            if operation == "attach":
                success = vrf_api.attach_vrf_to_switches(fabric_name, vrf_name, payload)
            else:
                success = vrf_api.detach_vrf_from_switches(fabric_name, vrf_name, payload)
            
            if success:
                MessageFormatter.success(f"VRF {operation.title()}", f"{vrf_name} (VLAN {vlan_id})", "")
                return True
            else:
                MessageFormatter.failure(f"VRF {operation.title()}", f"{vrf_name} (VLAN {vlan_id})", "")
                return False
                
        except Exception as e:
            MessageFormatter.error(f"VRF {operation}", f"{vrf_name}", e, "")
            return False

    def attach_vrf_by_name(self, vrf_name: str, fabric_name: str) -> bool:
        """Attach VRF to switches based on VRF name match in interface configurations."""
        return self.manage_vrf_by_name(vrf_name, fabric_name, "attach")

    def detach_vrf_by_name(self, vrf_name: str, fabric_name: str) -> bool:
        """Detach VRF from switches based on VRF name match in interface configurations."""
        return self.manage_vrf_by_name(vrf_name, fabric_name, "detach")

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
        try:
            action = "Attaching" if operation == "attach" else "Detaching"
            preposition = "to" if operation == "attach" else "from"
            print(f"\n=== {action} VRF {preposition} switch: {switch_name} ===")
            
            # Step 1: Load switch configuration
            switch_config, serial_number = self._load_switch_config(fabric_name, switch_role, switch_name)
            if not switch_config:
                return False
            
            # Step 2: Find VRF in switch interface configuration
            vrf_name = self._find_vrf_in_switch(switch_config, switch_name)
            if not vrf_name:
                return False
            
            print(f"Found VRF {vrf_name} in {switch_name} ({serial_number}) in {fabric_name}")
            
            # Step 3: Get VRF details from configuration
            vrf_details = self._find_vrf_by_name(vrf_name, fabric_name)
            if not vrf_details:
                print(f"❌ No VRF found with name '{vrf_name}' in fabric '{fabric_name}'")
                return False
            
            vlan_id = vrf_details.get("VLAN ID")
            
            # Step 4: Build switch info for payload
            switch_info = [{
                'hostname': switch_name,
                'serial_number': serial_number,
                'ip_address': switch_config.get('IP Address', ''),
                'role': switch_role,
                'vrf_name': vrf_name
            }]
            
            # Step 5: Build payload
            deployment = operation == "attach"
            payload = self._build_vrf_payload(vrf_name, vlan_id, switch_info, fabric_name, deployment)
            
            # Step 6: Execute operation
            if operation == "attach":
                success = vrf_api.attach_vrf_to_switches(fabric_name, vrf_name, payload)
            else:
                success = vrf_api.detach_vrf_from_switches(fabric_name, vrf_name, payload)
            
            if success:
                MessageFormatter.success(f"VRF {operation.title()}", f"{vrf_name} (VLAN {vlan_id}) {preposition} {switch_name}", "")
                return True
            else:
                MessageFormatter.failure(f"VRF {operation.title()}", f"{vrf_name} (VLAN {vlan_id}) {preposition} {switch_name}", "")
                return False
                
        except Exception as e:
            MessageFormatter.error(f"VRF {operation}", f"{switch_name}", e, "")
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

    def _find_switches_with_vrf_interface(self, vrf_name: str, fabric_name: str) -> List[Dict[str, Any]]:
        """Find all switches in the fabric that have int_routed_host interfaces with the specified VRF."""
        matching_switches = []
        fabric_path = self.builder.project_root / "network_configs" / "3_node" / fabric_name
        
        if not fabric_path.exists():
            print(f"❌ Fabric path not found: {fabric_path}")
            return matching_switches
        
        # Search through all roles
        for role_dir in fabric_path.iterdir():
            if role_dir.is_dir():
                role_name = role_dir.name
                
                # Search through all switches in this role
                for switch_file in role_dir.iterdir():
                    if switch_file.is_file() and switch_file.suffix == '.yaml':
                        switch_config = load_yaml_file(str(switch_file))
                        if switch_config and self._switch_has_vrf_interface(switch_config, vrf_name):
                            matching_switches.append({
                                'hostname': switch_file.stem,
                                'serial_number': switch_config.get('Serial Number', ''),
                                'ip_address': switch_config.get('IP Address', ''),
                                'role': role_name,
                                'vrf_name': vrf_name
                            })
        
        return matching_switches

    def _switch_has_vrf_interface(self, switch_config: Dict[str, Any], target_vrf: str) -> bool:
        """Check if a switch configuration has int_routed_host interfaces with the target VRF."""
        # Check Interface configurations for VRF
        interfaces = switch_config.get('Interface', [])
        if interfaces:
            for interface in interfaces:
                for int_name, int_config in interface.items():
                    # Check for int_routed_host policy AND matching VRF
                    if (int_config.get('policy') == 'int_routed_host' and
                        int_config.get('Interface VRF') == target_vrf):
                        return True
        
        return False

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
        switch_path = self.builder.project_root / "network_configs" / "3_node" / fabric_name / switch_role / f"{switch_name}.yaml"
        
        if not switch_path.exists():
            print(f"❌ Switch configuration not found: {switch_path}")
            return None, None
        
        switch_config = load_yaml_file(str(switch_path))
        if not switch_config:
            print(f"❌ Failed to load switch configuration: {switch_path}")
            return None, None
        
        serial_number = switch_config.get('Serial Number', '')
        if not serial_number:
            print(f"❌ No serial number found in switch configuration: {switch_name}")
            return None, None
        
        return switch_config, serial_number

    def _find_vrf_in_switch(self, switch_config: Dict[str, Any], switch_name: str) -> Optional[str]:
        """Find VRF name from switch interface configuration with int_routed_host policy."""
        interfaces = switch_config.get("Interface", [])
        
        # Handle list format where each interface is a single-key dict
        if isinstance(interfaces, list):
            for interface_item in interfaces:
                if isinstance(interface_item, dict):
                    # Each item in the list is a dict with one key (interface name)
                    for interface_name, interface_config in interface_item.items():
                        if isinstance(interface_config, dict):
                            policy = interface_config.get("policy")
                            if policy == "int_routed_host":
                                vrf_name = interface_config.get("Interface VRF")
                                if vrf_name:
                                    print(f"📋 Found interface {interface_name} with policy 'int_routed_host' and VRF '{vrf_name}'")
                                    return vrf_name
        
        # Also handle dict format for backward compatibility
        elif isinstance(interfaces, dict):
            for interface_name, interface_config in interfaces.items():
                if isinstance(interface_config, dict):
                    policy = interface_config.get("policy")
                    if policy == "int_routed_host":
                        vrf_name = interface_config.get("Interface VRF")
                        if vrf_name:
                            print(f"📋 Found interface {interface_name} with policy 'int_routed_host' and VRF '{vrf_name}'")
                            return vrf_name
        
        print(f"❌ No interface with 'int_routed_host' policy and VRF found in switch '{switch_name}'")
        return None

def main():
    """
    Main function for VRF attachment operations.
    """
    vrf_attachment = VRFAttachment()
    
    print("🔗  VRF Attachment - Network VRF Attachment Tool")
    print("=" * 60)
    
    # Configuration - Update these values as needed
    vrf_to_attach = "bluevrf"
    fabric_to_use = "Site1-Greenfield"
    
    # --- Attach VRF by Name ---
    
    # Attach VRF by name (automatically finds switches with matching VRF interface configurations)
    success = vrf_attachment.attach_vrf_by_name(vrf_to_attach, fabric_to_use)
    if not success:
        print(f"Failed to attach VRF '{vrf_to_attach}'")
        return 1
    
    print("\n🎉 VRF attachment process completed successfully!")
    return 0

if __name__ == "__main__":
    main_wrapper = create_main_function_wrapper("VRF Attachment", main)
    main_wrapper()
