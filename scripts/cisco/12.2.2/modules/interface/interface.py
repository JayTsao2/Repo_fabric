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
import time
import api.interface as interface_api
from modules.config_utils import load_yaml_file, read_freeform_config
from config.config_factory import config_factory
from typing import Dict, Set, Any

class InterfaceManager:
    """Unified interface operations manager with YAML configuration support."""
    
    def __init__(self):
        """Initialize with centralized configuration paths."""
        self.config_paths = config_factory.create_interface_config()
        self.config_base_path = self.config_paths['configs_dir']
        
        # Supported policy mappings
        self.supported_policies = {
            "int_access_host", "int_trunk_host", "int_routed_host",
            "int_port_channel_trunk_host", "int_port_channel_trunk_member_11_1",
            "int_port_channel_access_host", "int_port_channel_access_member_11_1"
        }
        
        # Default nvPairs for port channels
        self.pc_defaults = {
            "trunk": {
                "ADMIN_STATE": "true", "ALLOWED_VLANS": "all", "BPDUGUARD_ENABLED": "no",
                "DESC": "", "MTU": "jumbo", "PC_MODE": "active", "PO_ID": "",
                "PORTTYPE_FAST_ENABLED": "false", "SPEED": "Auto", "MEMBER_INTERFACES": "", "CONF": ""
            },
            "access": {
                "ADMIN_STATE": "true", "ACCESS_VLAN": "1", "BPDUGUARD_ENABLED": "true",
                "DESC": "", "MTU": "jumbo", "PC_MODE": "active", "PO_ID": "",
                "PORTTYPE_FAST_ENABLED": "true", "SPEED": "Auto", "MEMBER_INTERFACES": "", "CONF": ""
            }
        }
    
    def update_switch_interfaces(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Update all interfaces for a switch based on YAML configuration."""
        print(f"[Interface] Updating interfaces for switch: {switch_name} in fabric: {fabric_name}, role: {role}")
        
        try:
            # Load and validate configuration
            switch_config = self._load_config(fabric_name, role, switch_name)
            if not switch_config:
                return False
            
            # Get existing interfaces
            existing_data = interface_api.get_interfaces(serial_number=switch_config["Serial Number"], save_files=False)
            if not existing_data:
                print("[Interface] No existing interfaces found from NDFC")
                return False
            
            # Create maps
            existing_map = self._create_maps(existing_data, "existing")
            yaml_map = self._create_maps(switch_config["Interface"], "yaml")
            pc_mapping = self._create_port_channel_mapping(yaml_map)
            
            # Process all interfaces
            updated_interfaces = {policy: [] for policy in self.supported_policies}
            processed = set()
            
            # Process interfaces
            for name, config in yaml_map.items():
                is_pc = name.startswith(('Port-channel', 'port-channel'))
                self._process_interface(name, config, existing_map, updated_interfaces, processed, 
                                     pc_mapping, switch_config["Serial Number"], fabric_name, role, is_pc)
            
            # Handle unprocessed Ethernet interfaces
            self._process_unspecified_interfaces(existing_map, processed, updated_interfaces)
            
            # Delete orphaned port channels
            self._delete_orphaned_port_channels(existing_map, yaml_map, switch_config["Serial Number"])
            
            # Apply updates
            return self._apply_interface_updates(updated_interfaces)
            
        except Exception as e:
            print(f"[Interface] Error updating switch interfaces: {e}")
            return False
    
    def _load_config(self, fabric_name: str, role: str, switch_name: str) -> Dict[str, Any]:
        """Load and validate switch configuration from YAML file."""
        config_path = self.config_base_path / fabric_name / role / f"{switch_name}.yaml"
        print(f"[Interface] Loading switch configuration from: {config_path}")
        
        if not config_path.exists():
            print(f"[Interface] Switch configuration not found: {config_path}")
            return None
        
        switch_config = load_yaml_file(str(config_path))
        if not switch_config or "Interface" not in switch_config:
            print("[Interface] No interfaces found to process")
            return None
        
        if not switch_config.get("Serial Number"):
            print("[Interface] Error: No serial number found in switch config")
            return None
        
        return switch_config
    
    def _create_maps(self, data, map_type: str):
        """Create interface maps from data."""
        if map_type == "existing":
            interface_map = {}
            for policy_group in data:
                policy = policy_group.get("policy", "unknown")
                interfaces = policy_group.get("interfaces", [])
                if policy not in interface_map:
                    interface_map[policy] = {}
                for interface in interfaces:
                    interface_name = interface.get("ifName")
                    if interface_name:
                        interface_map[policy][interface_name] = interface
            return interface_map
        else:  # yaml
            yaml_map = {}
            for interface_config in data:
                for interface_name, interface_data in interface_config.items():
                    yaml_map[interface_name] = interface_data
            return yaml_map
    
    def _create_port_channel_mapping(self, yaml_map):
        """Create mapping of member interfaces to port channel names."""
        pc_mapping = {}
        for name, data in yaml_map.items():
            if name.startswith(('Port-channel', 'port-channel')):
                po_name = 'Port-channel' + name[12:] if name.startswith('port-channel') else name
                members_str = data.get("Port Channel Member Interfaces", "")
                if members_str:
                    members = self._parse_interfaces(members_str)
                    for member in members:
                        normalized = self._normalize_interface_name(member)
                        pc_mapping[normalized] = po_name
        return pc_mapping
    
    def _parse_interfaces(self, interfaces_str):
        """Parse interface string into list of interface names."""
        interfaces = []
        parts = [part.strip() for part in interfaces_str.split(',')]
        
        for part in parts:
            if '-' in part:
                start_part, end_part = part.split('-', 1)
                start_interface = self._normalize_interface_name(start_part.strip())
                end_num = end_part.strip()
                
                if '/' in start_interface:
                    base_part, start_num = start_interface.rsplit('/', 1)
                    try:
                        for i in range(int(start_num), int(end_num) + 1):
                            interfaces.append(f"{base_part}/{i}")
                    except ValueError:
                        interfaces.append(self._normalize_interface_name(part))
                else:
                    interfaces.append(self._normalize_interface_name(part))
            else:
                interfaces.append(self._normalize_interface_name(part))
        return interfaces
    
    def _normalize_interface_name(self, name):
        """Normalize interface name to standard format."""
        name = name.strip()
        if name.lower().startswith('e1/'):
            return name.replace('e1/', 'Ethernet1/', 1)
        elif name.lower().startswith('eth1/'):
            return name.replace('eth1/', 'Ethernet1/', 1)
        elif name.lower().startswith('ethernet1/'):
            return 'Ethernet1/' + name[10:]
        elif '/' not in name:
            return f"Ethernet1/{name}"
        return name
    
    def _process_interface(self, name, config, existing_map, updated_interfaces, processed, 
                          pc_mapping, serial_number, fabric_name, role, is_port_channel):
        """Process a single interface configuration."""
        print(f"[Interface] Processing interface: {name}")
        processed.add(name)
        
        policy = config.get("policy")
        if not policy:
            self._handle_no_policy_interface(name, config, existing_map, updated_interfaces, serial_number)
            return
        
        if policy not in self.supported_policies:
            print(f"[Interface] Warning: Policy '{policy}' not supported for interface {name}")
            return
        
        existing_interface = self._find_existing_interface(existing_map, name, policy)
        
        if existing_interface:
            interface_data = self._update_interface(existing_interface, config, name, pc_mapping, fabric_name, role)
        elif is_port_channel:
            interface_data = self._create_port_channel(serial_number, name, config, pc_mapping, fabric_name, role)
        else:
            print(f"[Interface] Warning: Interface {name} not found in existing interfaces")
            return
        
        if interface_data:
            updated_interfaces[policy].append(interface_data)
    
    def _handle_no_policy_interface(self, name, config, existing_map, updated_interfaces, serial_number):
        """Handle interfaces without policy - update description/admin state only."""
        existing_interface = self._find_existing_interface(existing_map, name, None)
        if not existing_interface:
            print(f"[Interface] Warning: Interface {name} not found")
            return
        
        # Get original policy
        policy_data = interface_api.get_interfaces(serial_number=serial_number, if_name=name, save_files=False)
        original_policy = None
        if policy_data:
            for data in policy_data:
                if data.get("policy"):
                    original_policy = data["policy"]
                    break
        
        if not original_policy:
            print(f"[Interface] Warning: Could not determine policy for interface {name}")
            return
        
        print(f"[Interface] Interface {name} has no policy specified, updating basic settings only")
        
        updated_nv_pairs = existing_interface["nvPairs"].copy()
        if "Interface Description" in config:
            updated_nv_pairs["DESC"] = str(config["Interface Description"]) if config["Interface Description"] else ""
        if "Enable Interface" in config:
            updated_nv_pairs["ADMIN_STATE"] = "true" if config["Enable Interface"] else "false"
        
        if original_policy not in updated_interfaces:
            updated_interfaces[original_policy] = []
        
        updated_interfaces[original_policy].append({
            "serialNumber": existing_interface["serialNumber"],
            "ifName": name,
            "nvPairs": updated_nv_pairs
        })
    
    def _find_existing_interface(self, existing_map, name, target_policy):
        """Find existing interface across all policies."""
        # Try target policy first
        if target_policy and target_policy in existing_map and name in existing_map[target_policy]:
            return existing_map[target_policy][name]
        
        # Search all policies
        for policy, interfaces in existing_map.items():
            if name in interfaces:
                return interfaces[name]
        
        # Try normalized search
        normalized_name = self._normalize_interface_name(name)
        for policy, interfaces in existing_map.items():
            for existing_name, interface_data in interfaces.items():
                if self._normalize_interface_name(existing_name) == normalized_name:
                    return interface_data
        
        return None
    
    def _update_interface(self, existing_interface, config, name, pc_mapping, fabric_name, role):
        """Update existing interface with YAML configuration."""
        updated_nv_pairs = self._update_nv_pairs(existing_interface["nvPairs"].copy(), config, 
                                                pc_mapping, name, fabric_name, role)
        
        return {
            "serialNumber": existing_interface["serialNumber"],
            "ifName": name,
            "nvPairs": updated_nv_pairs
        }
    
    def _create_port_channel(self, serial_number, name, config, pc_mapping, fabric_name, role):
        """Create new port channel interface."""
        policy = config.get("policy", "")
        
        if policy == "int_port_channel_access_host":
            default_nv_pairs = self.pc_defaults["access"].copy()
        else:
            default_nv_pairs = self.pc_defaults["trunk"].copy()
        
        updated_nv_pairs = self._update_nv_pairs(default_nv_pairs, config, pc_mapping, name, fabric_name, role)
        
        return {
            "serialNumber": serial_number,
            "ifName": name,
            "nvPairs": updated_nv_pairs
        }
    
    def _update_nv_pairs(self, nv_pairs, config, pc_mapping, interface_name, fabric_name, role):
        """Update nvPairs with configuration values."""
        # Common fields
        if "Interface Description" in config:
            nv_pairs["DESC"] = str(config["Interface Description"]) if config["Interface Description"] else ""
        if "Enable Interface" in config:
            nv_pairs["ADMIN_STATE"] = "true" if config["Enable Interface"] else "false"
        if "SPEED" in config:
            nv_pairs["SPEED"] = str(config["SPEED"])
        
        policy = config.get("policy", "")
        
        # Policy-specific updates
        if policy == "int_access_host":
            if "Access Vlan" in config:
                nv_pairs["ACCESS_VLAN"] = str(config["Access Vlan"])
            if "MTU" in config:
                nv_pairs["MTU"] = str(config["MTU"])
        
        elif policy == "int_trunk_host":
            if "Trunk Allowed Vlans" in config:
                allowed_vlans = config["Trunk Allowed Vlans"]
                if isinstance(allowed_vlans, (list, tuple)):
                    nv_pairs["ALLOWED_VLANS"] = ",".join(map(str, allowed_vlans))
                else:
                    nv_pairs["ALLOWED_VLANS"] = str(allowed_vlans) if allowed_vlans else "all"
            if "MTU" in config:
                nv_pairs["MTU"] = str(config["MTU"])
        
        elif policy == "int_routed_host":
            if "Interface IP" in config:
                nv_pairs["IP"] = str(config["Interface IP"]) if config["Interface IP"] else ""
            if "IP Netmask Length" in config:
                nv_pairs["PREFIX"] = str(config["IP Netmask Length"]) if config["IP Netmask Length"] else ""
            if "Interface VRF" in config:
                nv_pairs["INTF_VRF"] = str(config["Interface VRF"])
            if "MTU" in config:
                nv_pairs["MTU"] = str(config["MTU"])
        
        elif "port_channel" in policy and "host" in policy:
            # Port channel host
            nv_pairs["PO_ID"] = interface_name
            
            if "Port Channel Description" in config:
                nv_pairs["DESC"] = str(config["Port Channel Description"]) if config["Port Channel Description"] else ""
            if "Enable Port Channel" in config:
                nv_pairs["ADMIN_STATE"] = "true" if config["Enable Port Channel"] else "false"
            if "MTU" in config:
                nv_pairs["MTU"] = str(config["MTU"])
            if "Port Channel Mode" in config:
                nv_pairs["PC_MODE"] = str(config["Port Channel Mode"])
            if "Port Channel Member Interfaces" in config:
                nv_pairs["MEMBER_INTERFACES"] = str(config["Port Channel Member Interfaces"])
            if "Enable BPDU Guard" in config:
                nv_pairs["BPDUGUARD_ENABLED"] = "true" if config["Enable BPDU Guard"] else "no"
            if "Enable Port Type Fast" in config:
                nv_pairs["PORTTYPE_FAST_ENABLED"] = "true" if config["Enable Port Type Fast"] else "false"
            
            if "access" in policy and "Access Vlan" in config:
                nv_pairs["ACCESS_VLAN"] = str(config["Access Vlan"])
            elif "trunk" in policy and "Trunk Allowed Vlans" in config:
                allowed_vlans = config["Trunk Allowed Vlans"]
                if isinstance(allowed_vlans, (list, tuple)):
                    nv_pairs["ALLOWED_VLANS"] = ",".join(map(str, allowed_vlans))
                else:
                    nv_pairs["ALLOWED_VLANS"] = str(allowed_vlans) if allowed_vlans else "all"
        
        elif "port_channel" in policy and "member" in policy:
            # Port channel member
            if pc_mapping and interface_name:
                normalized_name = self._normalize_interface_name(interface_name)
                po_name = pc_mapping.get(normalized_name, "")
                if po_name:
                    nv_pairs["PO_ID"] = str(po_name)
                    print(f"[Interface] Set PO_ID={po_name} for member interface {interface_name}")
        
        # Handle freeform config
        if "Freeform Config" in config:
            freeform_path = config["Freeform Config"]
            if freeform_path:
                try:
                    switch_dir = self.config_base_path / fabric_name / role
                    freeform_full_path = switch_dir / freeform_path
                    print(f"[Interface] Loading freeform config from: {freeform_full_path}")
                    freeform_content = read_freeform_config(str(freeform_full_path))
                    nv_pairs["CONF"] = freeform_content
                except Exception as e:
                    print(f"[Interface] Warning: Failed to load freeform config {freeform_path}: {e}")
                    nv_pairs["CONF"] = ""
            else:
                nv_pairs["CONF"] = ""
        
        return nv_pairs
    
    def _process_unspecified_interfaces(self, existing_map, processed, updated_interfaces):
        """Set unspecified Ethernet interfaces to disabled trunk."""
        for policy, interfaces in existing_map.items():
            for name, existing_interface in interfaces.items():
                if (name not in processed and name.startswith('Ethernet') and 
                    not name.startswith(('Port-channel', 'port-channel'))):
                    
                    updated_nv_pairs = existing_interface["nvPairs"].copy()
                    updated_nv_pairs.update({
                        "ADMIN_STATE": "false",
                        "ALLOWED_VLANS": "none",
                        "MTU": "jumbo"
                    })
                    
                    updated_interfaces["int_trunk_host"].append({
                        "serialNumber": existing_interface["serialNumber"],
                        "ifName": name,
                        "nvPairs": updated_nv_pairs
                    })
    
    def _delete_orphaned_port_channels(self, existing_map, yaml_map, serial_number):
        """Delete port channels that exist in fabric but not in YAML."""
        existing_pcs = []
        for policy, interfaces in existing_map.items():
            if "port_channel" in policy and "host" in policy:
                for name in interfaces.keys():
                    if name.startswith(('Port-channel', 'port-channel')):
                        existing_pcs.append(name)
        
        yaml_pcs = set()
        for name in yaml_map.keys():
            if name.startswith(('Port-channel', 'port-channel')):
                normalized = 'Port-channel' + name[12:] if name.startswith('port-channel') else name
                yaml_pcs.add(normalized)
        
        pcs_to_delete = []
        for pc_name in existing_pcs:
            normalized = 'Port-channel' + pc_name[12:] if pc_name.startswith('port-channel') else pc_name
            if normalized not in yaml_pcs:
                pcs_to_delete.append({'ifName': pc_name, 'serialNumber': serial_number})
                print(f"[Interface] Port channel {pc_name} exists in fabric but not in YAML - marking for deletion")
        
        if pcs_to_delete:
            print(f"[Interface] Deleting {len(pcs_to_delete)} orphaned port channels")
            return interface_api.delete_interfaces(pcs_to_delete)
        return True
    
    def _apply_interface_updates(self, updated_interfaces):
        """Apply interface updates to NDFC."""
        
        for policy, interfaces in updated_interfaces.items():
            if not interfaces:
                continue
            
            print(f"[Interface] Applying updates for policy: {policy}")
            success = False
            count = 0
            while not success and count < 5:
                if interface_api.update_interface(policy=policy, interfaces_payload=interfaces):
                    print(f"[Interface] Successfully updated {len(interfaces)} interfaces for policy {policy}")
                    success = True
                else:
                    count = count + 1
                    print(f"[Interface] Failed to update interfaces for policy {policy}, retrying ({count}/5)")
                    time.sleep(5)  # Retry after delay

        
        return True
