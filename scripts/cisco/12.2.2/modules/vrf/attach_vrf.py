#!/usr/bin/env python3
"""
VRF Builder - Attachment Operations

This module handles VRF attachment/detachment operations:
- Attaching VRFs to switches based on VLAN ID
- Detaching VRFs from switches based on VLAN ID
- Managing switch discovery and payload generation
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path to access api and modules
sys.path.append(str(Path(__file__).parent.parent.absolute()))
import api.vrf as vrf_api
from modules.config_utils import load_yaml_file
from . import BaseVRFMethods

class VRFAttachment(BaseVRFMethods):
    """Handles VRF attachment and detachment operations."""
    
    def manage_vrf_by_vlan(self, vlan_id: int, fabric_name: str, operation: str = "attach") -> bool:
        """
        Attach or detach VRF to/from switches based on VLAN ID match in switch configurations.
        
        Args:
            vlan_id: VLAN ID to match in switch configurations
            fabric_name: Name of the fabric to search for switches
            operation: "attach" or "detach"
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            action = "Attaching" if operation == "attach" else "Detaching"
            preposition = "to" if operation == "attach" else "from"
            print(f"\n=== {action} VRF with VLAN {vlan_id} {preposition} switches in Fabric: {fabric_name} ===")
            
            # Step 1: Find the VRF with this VLAN ID
            vrf_name = self._find_vrf_by_vlan(vlan_id, fabric_name)
            if not vrf_name:
                print(f"❌ No VRF found with VLAN ID {vlan_id} in fabric {fabric_name}")
                return False
            
            print(f"📋 Found VRF: {vrf_name} with VLAN ID: {vlan_id}")
            
            # Step 2: Find switches with matching VLAN configuration
            matching_switches = self._find_switches_with_vlan(vlan_id, fabric_name)
            if not matching_switches:
                print(f"❌ No switches found with VLAN {vlan_id} in fabric {fabric_name}")
                return False
            
            print(f"📋 Found {len(matching_switches)} switches with VLAN {vlan_id}:")
            for switch in matching_switches:
                print(f"  - {switch['hostname']} ({switch['serial_number']}) - Role: {switch['role']}")
            
            # Step 3: Build payload
            deployment = operation == "attach"
            payload = self._build_vrf_payload(vrf_name, vlan_id, matching_switches, fabric_name, deployment)
            
            # Step 4: Execute operation
            if operation == "attach":
                success = vrf_api.attach_vrf_to_switches(fabric_name, vrf_name, payload)
                operation_desc = "attached to switches"
            else:
                success = vrf_api.detach_vrf_from_switches(fabric_name, vrf_name, payload)
                operation_desc = "detached from switches"
            
            if success:
                print(f"✅ SUCCESS: VRF VLAN {operation.title()} - {vrf_name} (VLAN {vlan_id})")
                print(f"   VRF '{vrf_name}' has been {operation_desc} successfully")
                return True
            else:
                print(f"❌ FAILED: VRF VLAN {operation.title()} - {vrf_name} (VLAN {vlan_id})")
                operation_verb = "attach" if operation == "attach" else "detach"
                print(f"   Failed to {operation_verb} VRF '{vrf_name}' to switches")
                return False
                
        except Exception as e:
            print(f"❌ Error {operation}ing VRF by VLAN {vlan_id}: {e}")
            return False

    def attach_vrf_by_vlan(self, vlan_id: int, fabric_name: str) -> bool:
        """Attach VRF to switches based on VLAN ID match."""
        return self.manage_vrf_by_vlan(vlan_id, fabric_name, "attach")

    def detach_vrf_by_vlan(self, vlan_id: int, fabric_name: str) -> bool:
        """Detach VRF from switches based on VLAN ID match."""
        return self.manage_vrf_by_vlan(vlan_id, fabric_name, "detach")

    def _find_vrf_by_vlan(self, vlan_id: int, fabric_name: str) -> Optional[str]:
        """Find VRF name by VLAN ID and fabric name."""
        config = self.builder.get_vrf_config()
        vrf_config_list = load_yaml_file(config.config_path)
        
        if isinstance(vrf_config_list, dict) and "VRF" in vrf_config_list:
            vrf_list = vrf_config_list["VRF"]
            for vrf in vrf_list:
                if (vrf.get("Fabric") == fabric_name and 
                    vrf.get("VLAN ID") == vlan_id):
                    return vrf.get("VRF Name")
        return None

    def _find_switches_with_vlan(self, vlan_id: int, fabric_name: str) -> List[Dict[str, Any]]:
        """Find all switches in the fabric that have the specified VLAN configured."""
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
                        if switch_config and self._switch_has_vlan(switch_config, vlan_id):
                            matching_switches.append({
                                'hostname': switch_file.stem,
                                'serial_number': switch_config.get('Serial Number', ''),
                                'ip_address': switch_config.get('IP Address', ''),
                                'role': role_name,
                                'vlan_id': vlan_id
                            })
        
        return matching_switches

    def _switch_has_vlan(self, switch_config: Dict[str, Any], target_vlan: int) -> bool:
        """Check if a switch configuration contains the target VLAN."""
        # Check top-level vlan field
        if switch_config.get('vlan') == target_vlan:
            return True
        
        # Check Interface configurations for VLAN
        interfaces = switch_config.get('Interface', [])
        if interfaces:
            for interface in interfaces:
                for int_name, int_config in interface.items():
                    # Check for VLAN in various possible fields
                    if (int_config.get('vlan') == target_vlan or
                        int_config.get('VLAN') == target_vlan or
                        int_config.get('VLAN ID') == target_vlan):
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

def main():
    """
    Main function for VRF attachment operations.
    """
    vrf_attachment = VRFAttachment()
    
    print("🔗  VRF Attachment - Network VRF Attachment Tool")
    print("=" * 60)
    
    # Configuration - Update these values as needed
    vlan_to_attach = 2000
    fabric_to_use = "Site3-Test"
    
    # --- Attach VRF by VLAN ---
    
    # Attach VRF by VLAN ID (automatically finds VRF and matching switches)
    success = vrf_attachment.attach_vrf_by_vlan(vlan_to_attach, fabric_to_use)
    if not success:
        print(f"Failed to attach VRF with VLAN {vlan_to_attach}")
        return 1
    
    print("\n🎉 VRF attachment process completed successfully!")
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
