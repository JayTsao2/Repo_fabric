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
from modules.config_utils import load_yaml_file
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
        
        print(f"Loading config: {config_path.name}")
        return load_yaml_file(str(config_path))
    
    def _load_freeform_config(self, fabric_name: str, role: str, switch_name: str, freeform_path: str) -> str:
        """Load freeform configuration from file."""
        # Construct full path relative to switch config directory
        switch_dir = self.config_base_path / fabric_name / role
        freeform_full_path = switch_dir / freeform_path
        
        try:
            if freeform_full_path.exists():
                with open(freeform_full_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            else:
                print(f"Freeform config not found: {freeform_full_path}")
                return ""
        except Exception as e:
            print(f"Error loading freeform config: {e}")
            return ""
    
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
        nv_pairs["PTP"] = "false"
        nv_pairs["ENABLE_NETFLOW"] = "false"
        nv_pairs["NETFLOW_MONITOR"] = ""
        nv_pairs["POLICY_DESC"] = ""
        nv_pairs["CONF"] = ""
        
        # Policy-specific configurations
        if policy == "int_access_host":
            # Access port specific fields
            nv_pairs["ACCESS_VLAN"] = str(interface_data.get("Access Vlan", "1"))
            nv_pairs["MTU"] = str(interface_data.get("MTU", "jumbo"))
            nv_pairs["PRIORITY"] = "500"
            nv_pairs["BPDUGUARD_ENABLED"] = "true"
            nv_pairs["PORTTYPE_FAST_ENABLED"] = "true"
            nv_pairs["CDP_ENABLE"] = "true"
            nv_pairs["ENABLE_ORPHAN_PORT"] = "false"
            nv_pairs["ENABLE_PFC"] = "false"
            nv_pairs["QUEUING_POLICY"] = ""
            nv_pairs["NETFLOW_SAMPLER"] = ""
            nv_pairs["ENABLE_QOS"] = "false"
            nv_pairs["PORT_DUPLEX_MODE"] = "auto"
            nv_pairs["QOS_POLICY"] = ""
            nv_pairs["ENABLE_MONITOR"] = "false"
            
        elif policy == "int_trunk_host":
            # Trunk port specific fields
            allowed_vlans = interface_data.get("Trunk Allowed Vlans", "all")
            if allowed_vlans and not (isinstance(allowed_vlans, str) and 'controlled by policy' in str(allowed_vlans).lower()):
                if isinstance(allowed_vlans, (list, tuple)):
                    nv_pairs["ALLOWED_VLANS"] = ",".join(map(str, allowed_vlans))
                else:
                    nv_pairs["ALLOWED_VLANS"] = str(allowed_vlans)
            else:
                nv_pairs["ALLOWED_VLANS"] = "none"
                
            nv_pairs["MTU"] = str(interface_data.get("MTU", "jumbo"))
            nv_pairs["PRIORITY"] = "450"
            nv_pairs["BPDUGUARD_ENABLED"] = "no"
            nv_pairs["PORTTYPE_FAST_ENABLED"] = "true"
            nv_pairs["GF"] = ""
            
        elif policy == "int_routed_host":
            # Routed port specific fields
            ip_value = interface_data.get("Interface IP")
            prefix_value = interface_data.get("IP Netmask Length")
            
            nv_pairs["IP"] = str(ip_value) if ip_value else ""
            nv_pairs["PREFIX"] = str(prefix_value) if prefix_value else ""
            nv_pairs["INTF_VRF"] = str(interface_data.get("Interface VRF", "default"))
            nv_pairs["MTU"] = str(interface_data.get("MTU", "9100"))
            nv_pairs["PRIORITY"] = "500"
            nv_pairs["ENABLE_PFC"] = "false"
            nv_pairs["ENABLE_PIM_SPARSE"] = "false"
            nv_pairs["PIM_DR_PRIORITY"] = "1"
            nv_pairs["QUEUING_POLICY"] = ""
            nv_pairs["NETFLOW_SAMPLER"] = ""
            nv_pairs["ENABLE_QOS"] = "false"
            nv_pairs["QOS_POLICY"] = ""
            nv_pairs["DISABLE_IP_REDIRECTS"] = "false"
            nv_pairs["ROUTING_TAG"] = ""
        
        # Handle freeform configuration
        if "Freeform Config" in interface_data:
            freeform_path = interface_data["Freeform Config"]
            freeform_content = self._load_freeform_config(fabric_name, role, switch_name, freeform_path)
            nv_pairs["CONF"] = freeform_content
        
        return nv_pairs
    
    def _parse_interfaces(self, switch_config: Dict[str, Any], fabric_name: str, 
                         role: str, switch_name: str) -> Dict[str, List[InterfaceConfig]]:
        """Parse switch interfaces and group by policy."""
        serial_number = switch_config.get("Serial Number", "")
        if not serial_number:
            print("No serial number found in switch config")
            return {}
        
        interfaces_by_policy = {
            "int_access_host": [],
            "int_trunk_host": [],
            "int_routed_host": []
        }
        
        if "Interface" not in switch_config:
            print("No interfaces found in config")
            return interfaces_by_policy
        
        for interface_config in switch_config["Interface"]:
            for interface_name, interface_data in interface_config.items():
                policy = interface_data.get("policy")
                
                if policy in interfaces_by_policy:
                    # print(f"Processing {interface_name} ({policy})")
                    
                    nv_pairs_dict = self._build_nv_pairs(
                        interface_name, interface_data, fabric_name, role, switch_name
                    )
                    
                    interface_config_obj = InterfaceConfig(
                        serial_number=serial_number,
                        if_name=interface_name,
                        policy=policy,
                        nv_pairs=nv_pairs_dict
                    )
                    
                    interfaces_by_policy[policy].append(interface_config_obj)
        
        return interfaces_by_policy
    
    def update_switch_interfaces(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Update all interfaces for a switch based on YAML configuration."""
        try:
            switch_config = self._load_switch_config(fabric_name, role, switch_name)
            if not switch_config:
                return False
            
            interfaces_by_policy = self._parse_interfaces(switch_config, fabric_name, role, switch_name)
            
            success = True
            total_updated = 0
            
            # Update interfaces grouped by policy
            for policy, interface_configs in interfaces_by_policy.items():
                if interface_configs:
                    # Convert to API format
                    interfaces_payload = [config.to_dict() for config in interface_configs]
                    
                    # Call API to update interfaces
                    if interface_api.update_interface(fabric_name, policy, interfaces_payload):
                        total_updated += len(interface_configs)
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
