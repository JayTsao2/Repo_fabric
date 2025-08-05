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
                role,
                serial_number
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
    
    def _create_port_channel_mapping(self, yaml_interfaces_map):
        """Create a mapping of member interfaces to their port channel name."""
        port_channel_mapping = {}
        
        for interface_name, interface_data in yaml_interfaces_map.items():
            if (interface_name.startswith('Port-channel') or interface_name.startswith('port-channel')):
                # Normalize port channel name to proper capitalization (Port-channel501)
                if interface_name.startswith('port-channel'):
                    # Convert lowercase to proper case
                    po_name = 'Port-channel' + interface_name[12:]  # Remove 'port-channel' and add 'Port-channel'
                else:
                    # Already properly capitalized
                    po_name = interface_name
                
                member_interfaces_str = interface_data.get("Port Channel Member Interfaces", "")
                if member_interfaces_str:
                    member_interfaces = self._parse_member_interfaces(member_interfaces_str)
                    for member_interface in member_interfaces:
                        # Normalize interface name for consistent mapping
                        normalized_member = self._normalize_interface_name(member_interface)
                        port_channel_mapping[normalized_member] = po_name
                        print(f"[Interface] Mapping member interface {normalized_member} to port channel {po_name}")
        
        return port_channel_mapping
    
    def _parse_member_interfaces(self, member_interfaces_str):
        """Parse member interfaces string to get list of interface names."""
        interfaces = []
        
        # Remove spaces and split by commas
        parts = [part.strip() for part in member_interfaces_str.split(',')]
        
        for part in parts:
            if '-' in part:
                # Handle ranges like "e1/17-20" or "Ethernet1/5-10"
                start_part, end_part = part.split('-', 1)
                start_interface = self._normalize_interface_name(start_part.strip())
                end_num = end_part.strip()
                
                # Extract the base and start number from start_interface
                if '/' in start_interface:
                    base_part, start_num = start_interface.rsplit('/', 1)
                    try:
                        start_num = int(start_num)
                        end_num = int(end_num)
                        for i in range(start_num, end_num + 1):
                            interfaces.append(f"{base_part}/{i}")
                    except ValueError:
                        # If parsing fails, just add the original part
                        interfaces.append(self._normalize_interface_name(part))
                else:
                    interfaces.append(self._normalize_interface_name(part))
            else:
                # Single interface
                interfaces.append(self._normalize_interface_name(part))
        
        return interfaces
    
    def _normalize_interface_name(self, interface_name):
        """Normalize interface name to standard format (Ethernet1/X)."""
        interface_name = interface_name.strip()
        
        # Handle different formats: e1/5, eth1/5, Ethernet1/5
        if interface_name.lower().startswith('e1/'):
            return interface_name.replace('e1/', 'Ethernet1/', 1)
        elif interface_name.lower().startswith('eth1/'):
            return interface_name.replace('eth1/', 'Ethernet1/', 1)
        elif interface_name.lower().startswith('ethernet1/'):
            # Already in correct format, but ensure proper case
            return 'Ethernet1/' + interface_name[10:]
        else:
            # Default case - assume it's already correct or add Ethernet1/ prefix if needed
            if '/' not in interface_name:
                return f"Ethernet1/{interface_name}"
            return interface_name
    
    def _create_default_port_channel_nv_pairs(self):
        """Create default nvPairs for new port-channel interfaces."""
        return {
            "ADMIN_STATE": "true",
            "ALLOWED_VLANS": "all",
            "BPDUGUARD_ENABLED": "no",
            "DESC": "",
            "MTU": "jumbo",
            "PC_MODE": "active",
            "PO_ID": "",  # Will be set to interface name
            "PORTTYPE_FAST_ENABLED": "false",
            "SPEED": "Auto",
            "MEMBER_INTERFACES": "",
            "CONF": ""
        }
    
    def _update_interfaces_from_yaml(self, existing_interfaces_map, yaml_interfaces_map, fabric_name, role, serial_number):
        """Update existing interface nvPairs based on YAML configuration."""
        updated_interfaces = {
            "int_access_host": [],
            "int_trunk_host": [],
            "int_routed_host": [],
            "int_port_channel_trunk_host": [],
            "int_port_channel_trunk_member_11_1": []
        }
        
        # Track which interfaces were processed from YAML
        processed_interfaces = set()
        
        # Create port channel mapping for member interface processing
        port_channel_mapping = self._create_port_channel_mapping(yaml_interfaces_map)
        
        # First, process port-channel interfaces (logical interfaces first)
        port_channel_interfaces = {k: v for k, v in yaml_interfaces_map.items() 
                                 if k.startswith('Port-channel') or k.startswith('port-channel')}
        
        for interface_name, yaml_config in port_channel_interfaces.items():
            print(f"[Interface] Processing port-channel interface: {interface_name}")
            processed_interfaces.add(interface_name)
            policy = yaml_config.get("policy")
            
            existing_interface = self._find_existing_interface(existing_interfaces_map, interface_name, policy)
            
            if existing_interface:
                updated_nv_pairs = self._update_nv_pairs(
                    existing_interface["nvPairs"].copy(), 
                    yaml_config, 
                    fabric_name, 
                    role,
                    None,  # port_channel_mapping not needed for host interfaces
                    interface_name
                )
                
                updated_interface = {
                    "serialNumber": existing_interface["serialNumber"],
                    "ifName": interface_name,
                    "nvPairs": updated_nv_pairs
                }
                if policy and policy in updated_interfaces:
                    updated_interfaces[policy].append(updated_interface)
            else:
                # Port-channel doesn't exist, create a new one
                print(f"[Interface] Creating new port-channel interface: {interface_name}")
                default_nv_pairs = self._create_default_port_channel_nv_pairs()
                updated_nv_pairs = self._update_nv_pairs(
                    default_nv_pairs, 
                    yaml_config, 
                    fabric_name, 
                    role,
                    None,  # port_channel_mapping not needed for host interfaces
                    interface_name
                )
                
                new_interface = {
                    "serialNumber": serial_number,
                    "ifName": interface_name,
                    "nvPairs": updated_nv_pairs
                }
                if policy and policy in updated_interfaces:
                    updated_interfaces[policy].append(new_interface)
        
        # Then process regular interfaces (excluding port-channels)
        regular_interfaces = {k: v for k, v in yaml_interfaces_map.items() 
                            if not (k.startswith('Port-channel') or k.startswith('port-channel'))}
        
        for interface_name, yaml_config in regular_interfaces.items():
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
                    role,
                    port_channel_mapping,
                    interface_name
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
        
        for policy, interfaces in existing_interfaces_map.items():
            for interface_name, existing_interface in interfaces.items():
                is_port_channel = interface_name.startswith(('Port-channel', 'port-channel'))
                is_processed = interface_name in processed_interfaces
                is_excluded = interface_name.startswith(('mgmt', 'loopback', 'nve'))
                
                
                if (not is_processed and not is_excluded and not is_port_channel):
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
        
        # Try case-insensitive and format variations
        normalized_search_name = self._normalize_interface_name(interface_name)
        
        for policy, interfaces in existing_interfaces_map.items():
            for existing_name, interface_data in interfaces.items():
                normalized_existing = self._normalize_interface_name(existing_name)
                if normalized_existing == normalized_search_name:
                    return interface_data
        return None
    
    def _update_nv_pairs(self, existing_nv_pairs, yaml_config, fabric_name, role, port_channel_mapping=None, interface_name=None):
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
        elif policy == "int_port_channel_trunk_host":
            self._update_port_channel_host_nv_pairs(existing_nv_pairs, yaml_config, interface_name)
        elif policy == "int_port_channel_trunk_member_11_1":
            self._update_port_channel_member_nv_pairs(existing_nv_pairs, yaml_config, port_channel_mapping, interface_name)
        
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
    
    def _update_port_channel_host_nv_pairs(self, nv_pairs, yaml_config, interface_name=None):
        """Update nvPairs for port channel host interfaces."""
        # Set PO_ID to the port channel interface name itself
        if interface_name:
            nv_pairs["PO_ID"] = interface_name
            print(f"[Interface] Set PO_ID={interface_name} for port channel host interface")
        
        # Update port channel description
        if "Port Channel Description" in yaml_config:
            desc_value = yaml_config["Port Channel Description"]
            nv_pairs["DESC"] = str(desc_value) if desc_value else ""
        
        # Update enable port channel (admin state)
        if "Enable Port Channel" in yaml_config:
            nv_pairs["ADMIN_STATE"] = "true" if yaml_config["Enable Port Channel"] else "false"
        
        # Update trunk allowed VLANs
        if "Trunk Allowed Vlans" in yaml_config:
            allowed_vlans = yaml_config["Trunk Allowed Vlans"]
            if isinstance(allowed_vlans, (list, tuple)):
                nv_pairs["ALLOWED_VLANS"] = ",".join(map(str, allowed_vlans))
            else:
                nv_pairs["ALLOWED_VLANS"] = str(allowed_vlans) if allowed_vlans else "all"
        
        # Update MTU
        if "MTU" in yaml_config:
            nv_pairs["MTU"] = str(yaml_config["MTU"])
        
        # Update port channel mode
        if "Port Channel Mode" in yaml_config:
            nv_pairs["PC_MODE"] = str(yaml_config["Port Channel Mode"])
        
        # Update member interfaces
        if "Port Channel Member Interfaces" in yaml_config:
            nv_pairs["MEMBER_INTERFACES"] = str(yaml_config["Port Channel Member Interfaces"])
        
        # Update BPDU Guard
        if "Enable BPDU Guard" in yaml_config:
            nv_pairs["BPDUGUARD_ENABLED"] = "true" if yaml_config["Enable BPDU Guard"] else "no"
        
        # Update Port Type Fast
        if "Enable Port Type Fast" in yaml_config:
            nv_pairs["PORTTYPE_FAST_ENABLED"] = "true" if yaml_config["Enable Port Type Fast"] else "false"
    
    def _update_port_channel_member_nv_pairs(self, nv_pairs, yaml_config, port_channel_mapping=None, interface_name=None):
        """Update nvPairs for port channel member interfaces."""
        # Update port channel ID - this is critical for validation
        # Use the current interface name to look up the full port channel name
        if port_channel_mapping and interface_name:
            normalized_name = self._normalize_interface_name(interface_name)
            po_name = port_channel_mapping.get(normalized_name, "")
            if po_name:
                nv_pairs["PO_ID"] = str(po_name)
                print(f"[Interface] Set PO_ID={po_name} for member interface {interface_name}")
            else:
                print(f"Warning: Could not find port channel name for member interface {interface_name}")
        return nv_pairs
    
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
        
        # Define the order to process policies - port channels first
        policy_order = [
            "int_port_channel_trunk_host",
            "int_port_channel_trunk_member_11_1", 
            "int_access_host",
            "int_trunk_host",
            "int_routed_host"
        ]
        
        for policy in policy_order:
            interfaces = updated_interfaces.get(policy, [])
            if not interfaces:
                continue
            
            print(f"[Interface] Updating {len(interfaces)} {policy} interfaces")
            
            # For port channel host policy, try PUT first, then POST if it fails
            if policy == "int_port_channel_trunk_host":
                if not self._update_port_channel_interfaces(policy, interfaces):
                    print(f"[Interface] Failed to update {policy} interfaces")
                    success = False
            else:
                # For other policies, use regular update
                if not interface_api.update_interface(policy, interfaces):
                    print(f"[Interface] Failed to update {policy} interfaces")
                    success = False
        
        return success
    
    def _update_port_channel_interfaces(self, policy, interfaces):
        """Update port channel interfaces with PUT first, then POST fallback."""
        # Try PUT request first
        if interface_api.update_interface(policy, interfaces):
            print(f"[Interface] Successfully updated {len(interfaces)} {policy} interfaces via PUT")
            return True
        
        # If PUT fails, try POST request
        print(f"[Interface] PUT failed for {policy}, trying POST...")
        try:
            result = interface_api.create_interface(policy, interfaces)
            
            if result:
                print(f"[Interface] Successfully created {len(interfaces)} {policy} interfaces via POST")
                return True
            else:
                print(f"[Interface] POST also failed for {policy}")
                return False
        except Exception as e:
            print(f"[Interface] Error during POST for {policy}: {e}")
            return False
