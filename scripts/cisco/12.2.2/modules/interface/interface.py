#!/usr/bin/env python3
"""
Interface Manager - Unified Interface Management Interface

This module provides a clean, unified interface for all interface operations with:
- YAML-based interface configuration management
- Interface configuration updates using switch YAML files
- Freeform configuration integration
- Policy-based interface management (access, trunk, routed)
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import api.interface as interface_api
from modules.config_utils import load_yaml_file, read_freeform_config
from config.config_factory import config_factory

@dataclass
class InterfaceConfig:
    """Interface configuration data structure."""
    serial_number: str
    if_name: str
    policy: str
    nv_pairs: Dict[str, Any]  # Dict for API
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls."""
        return {
            "serialNumber": self.serial_number,
            "ifName": self.if_name,
            "nvPairs": self.nv_pairs
        }

class InterfaceManager:
    """Unified interface operations manager with YAML configuration support."""
    
    def __init__(self):
        """Initialize with centralized configuration paths."""
        self.config_paths = config_factory.create_interface_config()
        self.config_base_path = self.config_paths['configs_dir']
    
    def _load_switch_config(self, fabric_name: str, role: str, switch_name: str) -> Optional[Dict[str, Any]]:
        """Load switch configuration from YAML file."""
        config_path = self.config_base_path / fabric_name / role / f"{switch_name}.yaml"
        
        if not config_path.exists():
            print(f"Switch configuration not found: {config_path}")
            return None
        
        print(f"Loading config: {config_path}")
        return load_yaml_file(str(config_path))
    
    def _load_freeform_config(self, fabric_name: str, role: str, freeform_path: str) -> str:
        """Load freeform configuration from file."""
        # Construct full path relative to switch config directory
        switch_dir = self.config_base_path / fabric_name / role
        freeform_full_path = switch_dir / freeform_path
        print(f"Loading freeform config from: {freeform_full_path}")
        # Use config_utils for consistent file loading with special banner handling
        return read_freeform_config(str(freeform_full_path))
    
    def _build_nv_pairs(self, interface_name: str, interface_data: Dict[str, Any], 
                       fabric_name: str, role: str, switch_name: str) -> Dict[str, Any]:
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
            # Access port specific fields
            nv_pairs["ACCESS_VLAN"] = str(interface_data.get("Access Vlan", "1"))
            nv_pairs["MTU"] = str(interface_data.get("MTU", "jumbo"))
            nv_pairs["BPDUGUARD_ENABLED"] = "true"
            nv_pairs["PORTTYPE_FAST_ENABLED"] = "true"
            
        elif policy == "int_trunk_host":
            # Trunk port specific fields
            allowed_vlans = interface_data.get("Trunk Allowed Vlans", "all")
            if allowed_vlans and not (isinstance(allowed_vlans, str) and 'controlled by policy' in str(allowed_vlans).lower()):
                if isinstance(allowed_vlans, (list, tuple)):
                    nv_pairs["ALLOWED_VLANS"] = ",".join(map(str, allowed_vlans))
                else:
                    nv_pairs["ALLOWED_VLANS"] = str(allowed_vlans)
            else:
                nv_pairs["ALLOWED_VLANS"] = "all"
                
            nv_pairs["MTU"] = str(interface_data.get("MTU", "jumbo"))
        elif policy == "int_routed_host":
            # Routed port specific fields
            ip_value = interface_data.get("Interface IP")
            prefix_value = interface_data.get("IP Netmask Length")
            
            nv_pairs["IP"] = str(ip_value) if ip_value else ""
            nv_pairs["PREFIX"] = str(prefix_value) if prefix_value else ""
            nv_pairs["INTF_VRF"] = str(interface_data.get("Interface VRF", "default"))
            nv_pairs["MTU"] = str(interface_data.get("MTU", "9100"))
        
        # Handle freeform configuration
        if "Freeform Config" in interface_data:
            freeform_path = interface_data["Freeform Config"]
            freeform_content = self._load_freeform_config(fabric_name, role, freeform_path)
            nv_pairs["CONF"] = freeform_content
        
        return nv_pairs
    
    def _parse_interfaces(self, switch_config: Dict[str, Any], fabric_name: str, 
                         role: str, switch_name: str) -> Dict[str, Any]:
        """Parse switch interfaces and separate by policy vs non-policy interfaces."""
        serial_number = switch_config.get("Serial Number", "")
        if not serial_number:
            print("No serial number found in switch config")
            return {"policy_interfaces": {}, "admin_interfaces": []}
        
        policy_interfaces = {
            "int_access_host": [],
            "int_trunk_host": [],
            "int_routed_host": []
        }
        
        admin_interfaces = []  # For interfaces without policies
        
        if "Interface" not in switch_config:
            print("No interfaces found in config")
            return {"policy_interfaces": policy_interfaces, "admin_interfaces": admin_interfaces}
        
        for interface_config in switch_config["Interface"]:
            for interface_name, interface_data in interface_config.items():
                policy = interface_data.get("policy")
                
                if policy and policy in policy_interfaces:
                    # Interface with policy - use regular update API
                    nv_pairs_dict = self._build_nv_pairs(
                        interface_name, interface_data, fabric_name, role, switch_name
                    )
                    
                    interface_config_obj = InterfaceConfig(
                        serial_number=serial_number,
                        if_name=interface_name,
                        policy=policy,
                        nv_pairs=nv_pairs_dict
                    )
                    
                    policy_interfaces[policy].append(interface_config_obj)
                    
                else:
                    # Interface without policy - use admin status API
                    enable_interface = interface_data.get("Enable Interface", True)
                    admin_interfaces.append({
                        "serialNumber": serial_number,
                        "ifName": interface_name,
                        "operation": "noshut" if enable_interface else "shut"
                    })
        
        return {"policy_interfaces": policy_interfaces, "admin_interfaces": admin_interfaces}
    
    def update_switch_interfaces(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Update all interfaces for a switch based on YAML configuration."""
        try:
            switch_config = self._load_switch_config(fabric_name, role, switch_name)
            if not switch_config:
                return False
            
            parsed_interfaces = self._parse_interfaces(switch_config, fabric_name, role, switch_name)
            policy_interfaces = parsed_interfaces["policy_interfaces"]
            admin_interfaces = parsed_interfaces["admin_interfaces"]
            
            success = True
            total_updated = 0
            
            # Update policy-based interfaces
            for policy, interface_configs in policy_interfaces.items():
                if interface_configs:
                    interfaces_payload = [config.to_dict() for config in interface_configs]
                    if interface_api.update_interface(fabric_name, policy, interfaces_payload):
                        total_updated += len(interface_configs)
                    else:
                        success = False
            
            # Update admin status interfaces
            if admin_interfaces:
                if self._update_admin_status_interfaces(admin_interfaces):
                    total_updated += len(admin_interfaces)
                else:
                    success = False
            
            if success and total_updated > 0:
                print(f"Successfully updated {total_updated} interfaces for {switch_name}")
            elif total_updated == 0:
                print(f"No interfaces to update for {switch_name}")
            
            return success
            
        except Exception as e:
            print(f"Error updating switch interfaces: {e}")
            return False
    
    def _update_admin_status_interfaces(self, admin_interfaces: List[Dict[str, Any]]) -> bool:
        """Update admin status for interfaces without policies using dedicated API."""
        try:
            # Group interfaces by operation (shut/noshut)
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
                    if not interface_api.update_admin_status(payload):
                        print(f"Failed to {operation} interfaces: {[i['ifName'] for i in interfaces_for_operation]}")
                        return False
                    else:
                        print(f"Successfully {operation} interfaces: {[i['ifName'] for i in interfaces_for_operation]}")
            
            return True
            
        except Exception as e:
            print(f"Error updating admin status interfaces: {e}")
            return False
