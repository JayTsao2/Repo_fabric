#!/usr/bin/env python3
"""
Interface Manager - Unified Interface Management Interface

This module provides a clean, unified interface for all interface operations with:
- YAML-based interface configuration management
- Interface configuration updates using switch YAML files
- Freeform configuration integration
- Policy-based interface management (access, trunk, routed)
"""

import json
import api.interface as interface_api
from modules.config_utils import load_yaml_file, read_freeform_config
from config.config_factory import config_factory

class InterfaceManager:
    """Unified interface operations manager with YAML configuration support."""
    
    def __init__(self):
        """Initialize with centralized configuration paths."""
        self.config_paths = config_factory.create_interface_config()
        self.config_base_path = self.config_paths['configs_dir']
    
    def update_switch_interfaces(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Update all interfaces for a switch based on YAML configuration."""
        print(f"[Interface] Updating interfaces for switch: {switch_name} in fabric: {fabric_name}, role: {role}")
        
        try:
            # Load switch configuration
            config_path = self.config_base_path / fabric_name / role / f"{switch_name}.yaml"
            print(f"[Interface] Loading switch configuration from: {config_path}")
            if not config_path.exists():
                print(f"[Interface] Switch configuration not found: {config_path}")
                return False
            
            switch_config = load_yaml_file(str(config_path))
            if not switch_config or "Interface" not in switch_config:
                print("[Interface] No interfaces found to process")
                return True
            
            serial_number = switch_config.get("Serial Number", "")
            if not serial_number:
                print("[Interface] Error: No serial number found in switch config")
                return False
            
            # Get all existing interfaces from NDFC for this switch
            print(f"[Interface] Fetching existing interfaces for serial number: {serial_number}")
            existing_interfaces_data = interface_api.get_interfaces(
                serial_number=serial_number, 
                save_by_policy=False
            )
            
            if not existing_interfaces_data:
                print("[Interface] No existing interfaces found from NDFC")
                return False
            
            # Create a map of existing interfaces by name and policy for easy lookup
            existing_interfaces_map = self._create_interface_map(existing_interfaces_data)
            
            # Create YAML interface configuration map
            yaml_interfaces_map = self._create_yaml_interface_map(switch_config["Interface"])
            
            # Update interfaces based on YAML configuration
            updated_interfaces = self._update_interfaces_from_yaml(
                existing_interfaces_map, 
                yaml_interfaces_map, 
                fabric_name, 
                role
            )
            
            # Apply updates to NDFC
            return self._apply_interface_updates(updated_interfaces)
            
        except Exception as e:
            print(f"[Interface] Error updating switch interfaces: {e}")
            return False
    
    def _create_interface_map(self, existing_interfaces_data):
        """Create a map of existing interfaces organized by policy and interface name."""
        interface_map = {}
        
        for policy_group in existing_interfaces_data:
            policy = policy_group.get("policy", "unknown")
            interfaces = policy_group.get("interfaces", [])
            
            if policy not in interface_map:
                interface_map[policy] = {}
            
            for interface in interfaces:
                interface_name = interface.get("ifName")
                if interface_name:
                    interface_map[policy][interface_name] = interface
        
        return interface_map
    
    def _create_yaml_interface_map(self, yaml_interfaces):
        """Create a map of YAML interface configurations."""
        yaml_map = {}
        
        for interface_config in yaml_interfaces:
            for interface_name, interface_data in interface_config.items():
                yaml_map[interface_name] = interface_data
        
        return yaml_map
    
    def _update_interfaces_from_yaml(self, existing_interfaces_map, yaml_interfaces_map, fabric_name, role):
        """Update existing interface nvPairs based on YAML configuration."""
        updated_interfaces = {
            "int_access_host": [],
            "int_trunk_host": [],
            "int_routed_host": []
        }
        
        # Track which interfaces were processed from YAML
        processed_interfaces = set()
        
        # Process interfaces specified in YAML
        for interface_name, yaml_config in yaml_interfaces_map.items():
            print(f"[Interface] Processing interface: {interface_name}")
            processed_interfaces.add(interface_name)
            policy = yaml_config.get("policy")
            
            # Find existing interface in the appropriate policy group
            existing_interface = self._find_existing_interface(existing_interfaces_map, interface_name, policy)
            
            if existing_interface:
                # Update existing nvPairs with YAML configuration
                updated_nv_pairs = self._update_nv_pairs(
                    existing_interface["nvPairs"].copy(), 
                    yaml_config, 
                    fabric_name, 
                    role
                )
                
                updated_interface = {
                    "serialNumber": existing_interface["serialNumber"],
                    "ifName": interface_name,
                    "nvPairs": updated_nv_pairs
                }
                if policy and policy in updated_interfaces:
                    updated_interfaces[policy].append(updated_interface)
            else:
                print(f"[Interface] Warning: Interface {interface_name} not found in existing interfaces")
        
        # Process interfaces NOT specified in YAML - set to trunk with VLAN none and admin down
        self._process_unspecified_interfaces(existing_interfaces_map, processed_interfaces, updated_interfaces)
        
        return updated_interfaces
    
    def _process_unspecified_interfaces(self, existing_interfaces_map, processed_interfaces, updated_interfaces):
        """Process interfaces that are not specified in YAML configuration."""
        
        for interfaces in existing_interfaces_map.values():
            for interface_name, existing_interface in interfaces.items():
                if (interface_name not in processed_interfaces and 
                    not interface_name.startswith(('mgmt', 'loopback', 'nve'))):
                    updated_nv_pairs = existing_interface["nvPairs"].copy()
                    updated_nv_pairs.update({
                        "ADMIN_STATE": "false",
                        "ALLOWED_VLANS": "none",
                        "MTU": "jumbo"
                    })
                    
                    updated_interfaces["int_trunk_host"].append({
                        "serialNumber": existing_interface["serialNumber"],
                        "ifName": interface_name,
                        "nvPairs": updated_nv_pairs
                    })
    
    def _find_existing_interface(self, existing_interfaces_map, interface_name, target_policy):
        """Find existing interface across all policy groups."""
        # First try to find in the target policy
        if target_policy and target_policy in existing_interfaces_map:
            if interface_name in existing_interfaces_map[target_policy]:
                return existing_interfaces_map[target_policy][interface_name]
        
        # If not found in target policy, search across all policies
        for policy, interfaces in existing_interfaces_map.items():
            if interface_name in interfaces:
                return interfaces[interface_name]
        
        return None
    
    def _update_nv_pairs(self, existing_nv_pairs, yaml_config, fabric_name, role):
        """Update existing nvPairs with values from YAML configuration."""
        # Update common fields
        if "Interface Description" in yaml_config:
            desc_value = yaml_config["Interface Description"]
            existing_nv_pairs["DESC"] = str(desc_value) if desc_value else ""
        
        if "Enable Interface" in yaml_config:
            existing_nv_pairs["ADMIN_STATE"] = "true" if yaml_config["Enable Interface"] else "false"
        
        if "SPEED" in yaml_config:
            existing_nv_pairs["SPEED"] = str(yaml_config["SPEED"])
        
        # Update policy-specific fields
        policy = yaml_config.get("policy", "")
        
        if policy == "int_access_host":
            self._update_access_host_nv_pairs(existing_nv_pairs, yaml_config)
        elif policy == "int_trunk_host":
            self._update_trunk_host_nv_pairs(existing_nv_pairs, yaml_config)
        elif policy == "int_routed_host":
            self._update_routed_host_nv_pairs(existing_nv_pairs, yaml_config)
        
        # Handle freeform configuration
        self._update_freeform_config(existing_nv_pairs, yaml_config, fabric_name, role)
        
        return existing_nv_pairs
    
    def _update_access_host_nv_pairs(self, nv_pairs, yaml_config):
        """Update nvPairs for access host interfaces."""
        if "Access Vlan" in yaml_config:
            nv_pairs["ACCESS_VLAN"] = str(yaml_config["Access Vlan"])
        
        if "MTU" in yaml_config:
            nv_pairs["MTU"] = str(yaml_config["MTU"])
    
    def _update_trunk_host_nv_pairs(self, nv_pairs, yaml_config):
        """Update nvPairs for trunk host interfaces."""
        if "Trunk Allowed Vlans" in yaml_config:
            allowed_vlans = yaml_config["Trunk Allowed Vlans"]
            if isinstance(allowed_vlans, (list, tuple)):
                nv_pairs["ALLOWED_VLANS"] = ",".join(map(str, allowed_vlans))
            else:
                nv_pairs["ALLOWED_VLANS"] = str(allowed_vlans) if allowed_vlans else "all"
        
        if "MTU" in yaml_config:
            nv_pairs["MTU"] = str(yaml_config["MTU"])
    
    def _update_routed_host_nv_pairs(self, nv_pairs, yaml_config):
        """Update nvPairs for routed host interfaces."""
        if "Interface IP" in yaml_config:
            ip_value = yaml_config["Interface IP"]
            nv_pairs["IP"] = str(ip_value) if ip_value else ""
        
        if "IP Netmask Length" in yaml_config:
            prefix_value = yaml_config["IP Netmask Length"]
            nv_pairs["PREFIX"] = str(prefix_value) if prefix_value else ""
        
        if "Interface VRF" in yaml_config:
            nv_pairs["INTF_VRF"] = str(yaml_config["Interface VRF"])
        
        if "MTU" in yaml_config:
            nv_pairs["MTU"] = str(yaml_config["MTU"])
    
    def _update_freeform_config(self, nv_pairs, yaml_config, fabric_name, role):
        """Update freeform configuration in nvPairs."""
        if "Freeform Config" not in yaml_config:
            return
        
        freeform_path = yaml_config["Freeform Config"]
        if not freeform_path:
            nv_pairs["CONF"] = ""
            return
        
        try:
            switch_dir = self.config_base_path / fabric_name / role
            freeform_full_path = switch_dir / freeform_path
            print(f"[Interface] Loading freeform config from: {freeform_full_path}")
            freeform_content = read_freeform_config(str(freeform_full_path))
            nv_pairs["CONF"] = freeform_content
        except Exception as e:
            print(f"[Interface] Warning: Failed to load freeform config {freeform_path}: {e}")
            nv_pairs["CONF"] = ""
    
    def _apply_interface_updates(self, updated_interfaces):
        """Apply interface updates to NDFC."""
        success = True
        
        for policy, interfaces in updated_interfaces.items():
            if not interfaces:
                continue
            
            print(f"[Interface] Updating {len(interfaces)} {policy} interfaces")
            if not interface_api.update_interface(policy, interfaces):
                print(f"[Interface] Failed to update {policy} interfaces")
                success = False
        
        return success
