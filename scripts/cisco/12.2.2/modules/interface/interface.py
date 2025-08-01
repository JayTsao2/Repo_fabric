#!/usr/bin/env python3
"""
Interface Manager - Unified Interface Management Interface

This module provides a clean, unified interface for all interface operations with:
- YAML-based interface configuration management
- Interface configuration updates using switch YAML files
- Freeform configuration integration
- Policy-based interface management (access, trunk, routed)
"""

from typing import Dict, Any

import api.interface as interface_api
from modules.config_utils import load_yaml_file, read_freeform_config
from config.config_factory import config_factory

class InterfaceManager:
    """Unified interface operations manager with YAML configuration support."""
    
    def __init__(self):
        """Initialize with centralized configuration paths."""
        self.config_paths = config_factory.create_interface_config()
        self.config_base_path = self.config_paths['configs_dir']
        # Initialize interface API
        self.interface_api = interface_api
    
    def update_switch_interfaces(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Update all interfaces for a switch based on YAML configuration."""
        print(f"[Interface] Updating interfaces for switch: {switch_name} in fabric: {fabric_name}, role: {role}")
        
        try:
            # Load switch configuration
            config_path = self.config_base_path / fabric_name / role / f"{switch_name}.yaml"
            if not config_path.exists():
                print(f"[Interface] Switch configuration not found: {config_path}")
                return False
            
            switch_config = load_yaml_file(str(config_path))
            if not switch_config:
                return False
            
            serial_number = switch_config.get("Serial Number", "")
            if not serial_number:
                print("[Interface] Error: No serial number found in switch config")
                return False
            
            if "Interface" not in switch_config:
                print("[Interface] No interfaces found to process")
                return True  # No interfaces to process is considered success
            
            # Organize interfaces by policy type
            policy_interfaces = {
                "int_access_host": [],
                "int_trunk_host": [],
                "int_routed_host": []
            }
            admin_interfaces = []
            
            # Process all interfaces
            for interface_config in switch_config["Interface"]:
                for interface_name, interface_data in interface_config.items():
                    policy = interface_data.get("policy")
                    
                    if policy and policy in policy_interfaces:
                        # Build interface payload for policy-based interfaces
                        nv_pairs = self._build_nv_pairs(interface_name, interface_data, fabric_name, role)
                        
                        interface_payload = {
                            "serialNumber": serial_number,
                            "ifName": interface_name,
                            "nvPairs": nv_pairs
                        }
                        
                        policy_interfaces[policy].append(interface_payload)
                    else:
                        # Handle interfaces without policies (admin status only)
                        enable_interface = interface_data.get("Enable Interface", True)
                        admin_interfaces.append({
                            "serialNumber": serial_number,
                            "ifName": interface_name,
                            "operation": "noshut" if enable_interface else "shut"
                        })
            
            success = True
            total_updated = 0
            
            # Update policy-based interfaces
            for policy, interfaces in policy_interfaces.items():
                if interfaces:
                    if self.interface_api.update_interface(fabric_name, policy, interfaces):
                        total_updated += len(interfaces)
                        print(f"[Interface] Successfully updated {len(interfaces)} {policy} interfaces")
                    else:
                        print(f"[Interface] Failed to update {policy} interfaces")
                        success = False
            
            # Update admin status interfaces
            if admin_interfaces:
                # Group by operation type
                for operation in ["shut", "noshut"]:
                    interfaces_for_operation = [
                        {"serialNumber": intf["serialNumber"], "ifName": intf["ifName"]}
                        for intf in admin_interfaces if intf["operation"] == operation
                    ]
                    
                    if interfaces_for_operation:
                        payload = {
                            "operation": operation,
                            "interfaces": interfaces_for_operation
                        }
                        
                        if self.interface_api.update_admin_status(payload):
                            total_updated += len(interfaces_for_operation)
                            print(f"[Interface] Successfully {operation} {len(interfaces_for_operation)} interfaces")
                        else:
                            print(f"[Interface] Failed to {operation} interfaces")
                            success = False
            
            if success and total_updated > 0:
                print(f"[Interface] Successfully updated {total_updated} total interfaces for {switch_name}")
            elif total_updated == 0:
                print(f"[Interface] No interfaces to update for {switch_name}")
            
            return success
            
        except Exception as e:
            print(f"[Interface] Error updating switch interfaces: {e}")
            return False
    
    def _build_nv_pairs(self, interface_name: str, interface_data: Dict[str, Any], 
                       fabric_name: str, role: str) -> Dict[str, Any]:
        """Build nvPairs dictionary from interface data based on policy type."""
        policy = interface_data.get("policy", "")
        nv_pairs = {}
        
        # Common fields for all policies
        nv_pairs["INTF_NAME"] = interface_name
        nv_pairs["DESC"] = str(interface_data.get("Interface Description", "")) if interface_data.get("Interface Description") else ""
        nv_pairs["ADMIN_STATE"] = "true" if interface_data.get("Enable Interface", True) else "false"
        nv_pairs["SPEED"] = str(interface_data.get("SPEED", "Auto"))
        nv_pairs["NETFLOW_MONITOR"] = ""
        nv_pairs["POLICY_DESC"] = ""
        nv_pairs["CONF"] = ""
        
        # Policy-specific configurations
        if policy == "int_access_host":
            # Access port configuration
            nv_pairs["ACCESS_VLAN"] = str(interface_data.get("Access Vlan", "1"))
            nv_pairs["MTU"] = str(interface_data.get("MTU", "jumbo"))
            nv_pairs["BPDUGUARD_ENABLED"] = "true"
            nv_pairs["PORTTYPE_FAST_ENABLED"] = "true"
            
        elif policy == "int_trunk_host":
            # Trunk port configuration
            allowed_vlans = interface_data.get("Trunk Allowed Vlans", "all")
            if allowed_vlans and not isinstance(allowed_vlans, str):
                if isinstance(allowed_vlans, (list, tuple)):
                    nv_pairs["ALLOWED_VLANS"] = ",".join(map(str, allowed_vlans))
                else:
                    nv_pairs["ALLOWED_VLANS"] = str(allowed_vlans)
            else:
                nv_pairs["ALLOWED_VLANS"] = str(allowed_vlans) if allowed_vlans else "all"
                
            nv_pairs["MTU"] = str(interface_data.get("MTU", "jumbo"))
            
        elif policy == "int_routed_host":
            # Routed port configuration
            ip_value = interface_data.get("Interface IP")
            prefix_value = interface_data.get("IP Netmask Length")
            
            nv_pairs["IP"] = str(ip_value) if ip_value else ""
            nv_pairs["PREFIX"] = str(prefix_value) if prefix_value else ""
            nv_pairs["INTF_VRF"] = str(interface_data.get("Interface VRF", "default"))
            nv_pairs["MTU"] = str(interface_data.get("MTU", "9100"))
        
        # Handle freeform configuration
        if "Freeform Config" in interface_data:
            freeform_path = interface_data["Freeform Config"]
            try:
                # Construct full path relative to switch config directory
                switch_dir = self.config_base_path / fabric_name / role
                freeform_full_path = switch_dir / freeform_path
                print(f"[Interface] Loading freeform config from: {freeform_full_path}")
                freeform_content = read_freeform_config(str(freeform_full_path))
                nv_pairs["CONF"] = freeform_content
            except Exception as e:
                print(f"[Interface] Warning: Failed to load freeform config {freeform_path}: {e}")
                nv_pairs["CONF"] = ""
        
        return nv_pairs
