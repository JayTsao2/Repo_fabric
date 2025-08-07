#!/usr/bin/env python3
"""
Interface Manager - Unified Interface Management Interface

This module provides a clean, unified interface for all interface operations with:
- YAML-based interface configuration management
- Interface configuration updates using switch YAML files
- Freeform configuration integration
- Policy-based interface management (access, trunk, routed)
"""
import api.interface as interface_api
from modules.config_utils import load_yaml_file, read_freeform_config
from config.config_factory import config_factory
from dataclasses import dataclass
from typing import Dict, Set, Any

@dataclass
class InterfaceProcessingContext:
    """Context object to pass data between interface processing methods."""
    existing_interfaces_map: Dict[str, Dict[str, Any]]
    yaml_interfaces_map: Dict[str, Any]
    fabric_name: str
    role: str
    serial_number: str
    processed_interfaces: Set[str] = None
    port_channel_mapping: Dict[str, str] = None
    
    def __post_init__(self):
        if self.processed_interfaces is None:
            self.processed_interfaces = set()
        if self.port_channel_mapping is None:
            self.port_channel_mapping = {}

class InterfaceManager:
    """Unified interface operations manager with YAML configuration support."""
    
    def __init__(self):
        """Initialize with centralized configuration paths."""
        self.config_paths = config_factory.create_interface_config()
        self.config_base_path = self.config_paths['configs_dir']
    
    def _load_switch_config(self, fabric_name: str, role: str, switch_name: str) -> Dict[str, Any]:
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
        
        return switch_config
    
    def _extract_serial_number(self, switch_config: Dict[str, Any]) -> str:
        """Extract and validate serial number from switch configuration."""
        serial_number = switch_config.get("Serial Number", "")
        if not serial_number:
            print("[Interface] Error: No serial number found in switch config")
            return None
        return serial_number
    
    def _fetch_existing_interfaces(self, serial_number: str) -> list:
        """Fetch existing interfaces from NDFC for the given serial number."""
        print(f"[Interface] Fetching existing interfaces for serial number: {serial_number}")
        existing_interfaces_data = interface_api.get_interfaces(
            serial_number=serial_number, 
            save_files=False
        )
        
        if not existing_interfaces_data:
            print("[Interface] No existing interfaces found from NDFC")
            return None
        
        return existing_interfaces_data
    
    def _process_all_interfaces(self, context: InterfaceProcessingContext) -> Dict[str, list]:
        """Process all interfaces using the provided context."""
        updated_interfaces = self._initialize_interface_collections()
        
        # Process interfaces in order: port-channels first, then regular interfaces
        self._process_port_channel_interfaces(context, updated_interfaces)
        self._process_regular_interfaces(context, updated_interfaces)
        self._process_unspecified_interfaces(context.existing_interfaces_map, context.processed_interfaces, updated_interfaces)
        
        # Check for port channels that exist in fabric but not in YAML and mark for deletion
        self._process_port_channel_deletions(context)
        
        return updated_interfaces
    
    def _initialize_interface_collections(self) -> Dict[str, list]:
        """Initialize the interface collections for different policies."""
        return {
            "int_access_host": [],
            "int_trunk_host": [],
            "int_routed_host": [],
            "int_port_channel_trunk_host": [],
            "int_port_channel_trunk_member_11_1": [],
            "int_port_channel_access_host": [],
            "int_port_channel_access_member_11_1": []
        }
    
    def update_switch_interfaces(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Update all interfaces for a switch based on YAML configuration."""
        print(f"[Interface] Updating interfaces for switch: {switch_name} in fabric: {fabric_name}, role: {role}")
        
        try:
            switch_config = self._load_switch_config(fabric_name, role, switch_name)
            if not switch_config:
                return False
            
            serial_number = self._extract_serial_number(switch_config)
            if not serial_number:
                return False
            
            existing_interfaces_data = self._fetch_existing_interfaces(serial_number)
            if not existing_interfaces_data:
                return False
            
            context = InterfaceProcessingContext(
                existing_interfaces_map=self._create_interface_map(existing_interfaces_data),
                yaml_interfaces_map=self._create_yaml_interface_map(switch_config["Interface"]),
                fabric_name=fabric_name,
                role=role,
                serial_number=serial_number
            )
            
            updated_interfaces = self._process_all_interfaces(context)
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
    
    def _create_default_port_channel_access_nv_pairs(self):
        """Create default nvPairs for new port-channel access interfaces."""
        return {
            "ADMIN_STATE": "true",
            "ACCESS_VLAN": "1",
            "BPDUGUARD_ENABLED": "true",
            "DESC": "",
            "MTU": "jumbo",
            "PC_MODE": "active",
            "PO_ID": "",  # Will be set to interface name
            "PORTTYPE_FAST_ENABLED": "true",
            "SPEED": "Auto",
            "MEMBER_INTERFACES": "",
            "CONF": ""
        }
    
    def _process_port_channel_interfaces(self, context: InterfaceProcessingContext, updated_interfaces: Dict[str, list]):
        """Process port-channel interfaces from YAML configuration."""
        port_channel_interfaces = {k: v for k, v in context.yaml_interfaces_map.items() 
                                 if k.startswith('Port-channel') or k.startswith('port-channel')}
        
        for interface_name, yaml_config in port_channel_interfaces.items():
            print(f"[Interface] Processing port-channel interface: {interface_name}")
            context.processed_interfaces.add(interface_name)
            
            # Create mapping for this specific port channel's member interfaces
            single_pc_map = {interface_name: yaml_config}
            pc_mapping = self._create_port_channel_mapping(single_pc_map)
            context.port_channel_mapping.update(pc_mapping)
            
            policy = yaml_config.get("policy")
            
            # Check if policy is specified and supported/implemented
            if not policy:
                print(f"[Interface] Warning: Port-channel interface {interface_name} has no policy specified")
                continue
                
            if policy not in updated_interfaces:
                print(f"[Interface] Warning: Policy '{policy}' specified for port-channel interface {interface_name} is not implemented or supported")
                continue
            
            interface_data = self._create_or_update_interface(
                context, interface_name, yaml_config, is_port_channel=True
            )
            
            if interface_data:
                updated_interfaces[policy].append(interface_data)
    
    def _process_port_channel_deletions(self, context: InterfaceProcessingContext):
        """Check for existing port channels that are not specified in YAML and delete them."""
        # Find all existing port channels in the fabric
        existing_port_channels = []
        
        for policy, interfaces in context.existing_interfaces_map.items():
            # Only check port channel policies
            if "port_channel" in policy and "host" in policy:
                for interface_name, interface_data in interfaces.items():
                    if (interface_name.startswith('Port-channel') or interface_name.startswith('port-channel')):
                        existing_port_channels.append({
                            'ifName': interface_name,
                            'serialNumber': interface_data.get('serialNumber', context.serial_number),
                            'policy': policy
                        })
        
        if not existing_port_channels:
            print("[Interface] No existing port channels found in fabric")
            return
        
        # Check which port channels are not specified in YAML
        yaml_port_channels = set()
        for interface_name in context.yaml_interfaces_map.keys():
            if interface_name.startswith('Port-channel') or interface_name.startswith('port-channel'):
                # Normalize the name for comparison
                if interface_name.startswith('port-channel'):
                    normalized_name = 'Port-channel' + interface_name[12:]
                else:
                    normalized_name = interface_name
                yaml_port_channels.add(normalized_name)
        
        # Find port channels to delete (exist in fabric but not in YAML)
        port_channels_to_delete = []
        for pc_info in existing_port_channels:
            pc_name = pc_info['ifName']
            # Normalize for comparison
            if pc_name.startswith('port-channel'):
                normalized_name = 'Port-channel' + pc_name[12:]
            else:
                normalized_name = pc_name
            
            if normalized_name not in yaml_port_channels:
                port_channels_to_delete.append({
                    'ifName': pc_name,
                    'serialNumber': pc_info['serialNumber']
                })
                print(f"[Interface] Port channel {pc_name} exists in fabric but not in YAML - marking for deletion")
        
        # Delete the port channels if any found
        if port_channels_to_delete:
            print(f"[Interface] Deleting {len(port_channels_to_delete)} port channels that are not specified in YAML")
            return interface_api.delete_interfaces(port_channels_to_delete)
        else:
            print("[Interface] No port channels found for deletion")
            return True
    
    def _process_regular_interfaces(self, context: InterfaceProcessingContext, updated_interfaces: Dict[str, list]):
        """Process regular (non-port-channel) interfaces from YAML configuration."""
        regular_interfaces = {k: v for k, v in context.yaml_interfaces_map.items() 
                            if not (k.startswith('Port-channel') or k.startswith('port-channel'))}
        
        for interface_name, yaml_config in regular_interfaces.items():
            print(f"[Interface] Processing interface: {interface_name}")
            context.processed_interfaces.add(interface_name)
            
            policy = yaml_config.get("policy")
            
            # Handle interfaces without policy - only update description and admin status
            if not policy:
                self._process_interface_without_policy(context, interface_name, yaml_config, updated_interfaces)
                continue
            
            # Check if policy is supported/implemented
            if policy not in updated_interfaces:
                print(f"[Interface] Warning: Policy '{policy}' specified for interface {interface_name} is not implemented or supported")
                print(f"[Interface] Supported policies are: {', '.join(updated_interfaces.keys())}")
                continue
            
            interface_data = self._create_or_update_interface(
                context, interface_name, yaml_config, is_port_channel=False
            )
            
            if interface_data:
                updated_interfaces[policy].append(interface_data)
            else:
                print(f"[Interface] Warning: Interface {interface_name} not found in existing interfaces")
    
    def _process_interface_without_policy(self, context: InterfaceProcessingContext, interface_name: str, 
                                        yaml_config: Dict[str, Any], updated_interfaces: Dict[str, list]):
        """Process interfaces that don't have a policy specified - only update description and admin status."""
        # Find the existing interface across all policies
        existing_interface = self._find_existing_interface(context.existing_interfaces_map, interface_name, None)
        
        if not existing_interface:
            print(f"[Interface] Warning: Interface {interface_name} not found in existing interfaces")
            return
        
        # Get the original policy from the existing interface
        original_policy = self._find_interface_policy(context.existing_interfaces_map, interface_name)
        if not original_policy or original_policy not in updated_interfaces:
            print(f"[Interface] Warning: Could not determine original policy for interface {interface_name}")
            return
        
        print(f"[Interface] Interface {interface_name} does not have policy, updating description and admin status only")
        
        # Copy existing nvPairs and only update description and admin status
        updated_nv_pairs = existing_interface["nvPairs"].copy()
        
        # Update only description and admin status from YAML
        if "Interface Description" in yaml_config:
            desc_value = yaml_config["Interface Description"]
            updated_nv_pairs["DESC"] = str(desc_value) if desc_value else ""
        
        if "Enable Interface" in yaml_config:
            updated_nv_pairs["ADMIN_STATE"] = "true" if yaml_config["Enable Interface"] else "false"
        
        interface_data = {
            "serialNumber": existing_interface["serialNumber"],
            "ifName": interface_name,
            "nvPairs": updated_nv_pairs
        }
        
        updated_interfaces[original_policy].append(interface_data)
    
    def _find_interface_policy(self, existing_interfaces_map: Dict[str, Dict[str, Any]], interface_name: str) -> str:
        """Find which policy group an interface belongs to."""
        # First try exact name match
        for policy, interfaces in existing_interfaces_map.items():
            if interface_name in interfaces:
                return policy
        
        # Try normalized name match
        normalized_search_name = self._normalize_interface_name(interface_name)
        for policy, interfaces in existing_interfaces_map.items():
            for existing_name in interfaces.keys():
                normalized_existing = self._normalize_interface_name(existing_name)
                if normalized_existing == normalized_search_name:
                    return policy
        
        return None
    
    def _create_or_update_interface(self, context: InterfaceProcessingContext, interface_name: str, 
                                  yaml_config: Dict[str, Any], is_port_channel: bool) -> Dict[str, Any]:
        """Create or update a single interface based on YAML configuration."""
        policy = yaml_config.get("policy")
        existing_interface = self._find_existing_interface(context.existing_interfaces_map, interface_name, policy)
        
        if existing_interface:
            return self._update_existing_interface(context, existing_interface, yaml_config, interface_name)
        
        if is_port_channel:
            return self._create_new_port_channel_interface(context, interface_name, yaml_config)
        
        return None
    
    def _update_existing_interface(self, context: InterfaceProcessingContext, existing_interface: Dict[str, Any], 
                                 yaml_config: Dict[str, Any], interface_name: str) -> Dict[str, Any]:
        """Update an existing interface with YAML configuration."""
        updated_nv_pairs = self._update_nv_pairs(
            existing_interface["nvPairs"].copy(), 
            yaml_config, 
            context.fabric_name, 
            context.role,
            context.port_channel_mapping,
            interface_name
        )
        
        return {
            "serialNumber": existing_interface["serialNumber"],
            "ifName": interface_name,
            "nvPairs": updated_nv_pairs
        }
    
    def _create_new_port_channel_interface(self, context: InterfaceProcessingContext, interface_name: str, 
                                         yaml_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new port-channel interface."""
        policy = yaml_config.get("policy", "")
        
        # Choose appropriate default nvPairs based on policy
        if policy == "int_port_channel_access_host":
            default_nv_pairs = self._create_default_port_channel_access_nv_pairs()
        elif policy == "int_port_channel_trunk_host":
            default_nv_pairs = self._create_default_port_channel_nv_pairs()
        
        updated_nv_pairs = self._update_nv_pairs(
            default_nv_pairs, 
            yaml_config, 
            context.fabric_name, 
            context.role,
            None,  # port_channel_mapping not needed for host interfaces
            interface_name
        )
        
        return {
            "serialNumber": context.serial_number,
            "ifName": interface_name,
            "nvPairs": updated_nv_pairs
        }
    
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
        self._update_common_nv_pairs(existing_nv_pairs, yaml_config)
        
        # Update policy-specific fields
        policy = yaml_config.get("policy", "")
        policy_updaters = {
            "int_access_host": self._update_access_host_nv_pairs,
            "int_trunk_host": self._update_trunk_host_nv_pairs,
            "int_routed_host": self._update_routed_host_nv_pairs,
            "int_port_channel_trunk_host": lambda nv, cfg: self._update_port_channel_host_nv_pairs(nv, cfg, interface_name),
            "int_port_channel_trunk_member_11_1": lambda nv, cfg: self._update_port_channel_member_nv_pairs(nv, cfg, port_channel_mapping, interface_name),
            "int_port_channel_access_host": lambda nv, cfg: self._update_port_channel_access_host_nv_pairs(nv, cfg, interface_name),
            "int_port_channel_access_member_11_1": lambda nv, cfg: self._update_port_channel_access_member_nv_pairs(nv, cfg, port_channel_mapping, interface_name)
        }
        
        updater = policy_updaters.get(policy)
        if updater:
            updater(existing_nv_pairs, yaml_config)
        
        # Handle freeform configuration
        self._update_freeform_config(existing_nv_pairs, yaml_config, fabric_name, role)
        
        return existing_nv_pairs
    
    def _update_common_nv_pairs(self, nv_pairs: Dict[str, Any], yaml_config: Dict[str, Any]):
        """Update common nvPairs fields that apply to all interface types."""
        common_mappings = {
            "Interface Description": ("DESC", lambda x: str(x) if x else ""),
            "Enable Interface": ("ADMIN_STATE", lambda x: "true" if x else "false"),
            "SPEED": ("SPEED", str)
        }
        
        for yaml_key, (nv_key, converter) in common_mappings.items():
            if yaml_key in yaml_config:
                nv_pairs[nv_key] = converter(yaml_config[yaml_key])
    
    def _update_access_host_nv_pairs(self, nv_pairs, yaml_config):
        """Update nvPairs for access host interfaces."""
        mappings = {
            "Access Vlan": ("ACCESS_VLAN", str),
            "MTU": ("MTU", str)
        }
        self._apply_yaml_mappings(nv_pairs, yaml_config, mappings)
    
    def _update_trunk_host_nv_pairs(self, nv_pairs, yaml_config):
        """Update nvPairs for trunk host interfaces."""
        # Handle allowed VLANs with special processing
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
        mappings = {
            "Interface IP": ("IP", lambda x: str(x) if x else ""),
            "IP Netmask Length": ("PREFIX", lambda x: str(x) if x else ""),
            "Interface VRF": ("INTF_VRF", str),
            "MTU": ("MTU", str)
        }
        self._apply_yaml_mappings(nv_pairs, yaml_config, mappings)
    
    def _apply_yaml_mappings(self, nv_pairs: Dict[str, Any], yaml_config: Dict[str, Any], 
                           mappings: Dict[str, tuple]):
        """Apply YAML to nvPairs mappings using the provided mapping dictionary."""
        for yaml_key, (nv_key, converter) in mappings.items():
            if yaml_key in yaml_config:
                nv_pairs[nv_key] = converter(yaml_config[yaml_key])
    
    def _update_port_channel_host_nv_pairs(self, nv_pairs, yaml_config, interface_name=None):
        """Update nvPairs for port channel host interfaces."""
        # Set PO_ID to the port channel interface name itself
        if interface_name:
            nv_pairs["PO_ID"] = interface_name
            print(f"[Interface] Set PO_ID={interface_name} for port channel host interface")
        
        # Basic mappings
        basic_mappings = {
            "Port Channel Description": ("DESC", lambda x: str(x) if x else ""),
            "Enable Port Channel": ("ADMIN_STATE", lambda x: "true" if x else "false"),
            "MTU": ("MTU", str),
            "Port Channel Mode": ("PC_MODE", str),
            "Port Channel Member Interfaces": ("MEMBER_INTERFACES", str),
            "Enable BPDU Guard": ("BPDUGUARD_ENABLED", lambda x: "true" if x else "no"),
            "Enable Port Type Fast": ("PORTTYPE_FAST_ENABLED", lambda x: "true" if x else "false")
        }
        
        self._apply_yaml_mappings(nv_pairs, yaml_config, basic_mappings)
        
        # Handle allowed VLANs with special processing
        if "Trunk Allowed Vlans" in yaml_config:
            allowed_vlans = yaml_config["Trunk Allowed Vlans"]
            if isinstance(allowed_vlans, (list, tuple)):
                nv_pairs["ALLOWED_VLANS"] = ",".join(map(str, allowed_vlans))
            else:
                nv_pairs["ALLOWED_VLANS"] = str(allowed_vlans) if allowed_vlans else "all"
    
    def _update_port_channel_member_nv_pairs(self, nv_pairs, yaml_config, port_channel_mapping=None, interface_name=None):
        """Update nvPairs for port channel member interfaces."""
        # Update port channel ID - this is critical for validation
        # Use the current interface name to look up the full port channel name
        if not port_channel_mapping or not interface_name:
            print(f"Warning: Could not find port channel name for member interface {interface_name}")
            return nv_pairs
        
        normalized_name = self._normalize_interface_name(interface_name)
        po_name = port_channel_mapping.get(normalized_name, "")
        
        if not po_name:
            print(f"Warning: Could not find port channel name for member interface {interface_name}")
            return nv_pairs
        
        nv_pairs["PO_ID"] = str(po_name)
        print(f"[Interface] Set PO_ID={po_name} for member interface {interface_name}")
        return nv_pairs
    
    def _update_port_channel_access_host_nv_pairs(self, nv_pairs, yaml_config, interface_name=None):
        """Update nvPairs for port channel access host interfaces."""
        # Set PO_ID to the port channel interface name itself
        if interface_name:
            nv_pairs["PO_ID"] = interface_name
            print(f"[Interface] Set PO_ID={interface_name} for port channel access host interface")
        
        # Basic mappings for access port channel
        basic_mappings = {
            "Port Channel Description": ("DESC", lambda x: str(x) if x else ""),
            "Enable Port Channel": ("ADMIN_STATE", lambda x: "true" if x else "false"),
            "MTU": ("MTU", str),
            "Port Channel Mode": ("PC_MODE", str),
            "Port Channel Member Interfaces": ("MEMBER_INTERFACES", str),
            "Enable BPDU Guard": ("BPDUGUARD_ENABLED", lambda x: "true" if x else "no"),
            "Enable Port Type Fast": ("PORTTYPE_FAST_ENABLED", lambda x: "true" if x else "false"),
            "Access Vlan": ("ACCESS_VLAN", str)
        }
        
        self._apply_yaml_mappings(nv_pairs, yaml_config, basic_mappings)
    
    def _update_port_channel_access_member_nv_pairs(self, nv_pairs, yaml_config, port_channel_mapping=None, interface_name=None):
        """Update nvPairs for port channel access member interfaces."""
        # Update port channel ID - this is critical for validation
        # Use the current interface name to look up the full port channel name
        if not port_channel_mapping or not interface_name:
            print(f"Warning: Could not find port channel name for access member interface {interface_name}")
            return nv_pairs
        
        normalized_name = self._normalize_interface_name(interface_name)
        po_name = port_channel_mapping.get(normalized_name, "")
        
        if not po_name:
            print(f"Warning: Could not find port channel name for access member interface {interface_name}")
            return nv_pairs
        
        nv_pairs["PO_ID"] = str(po_name)
        print(f"[Interface] Set PO_ID={po_name} for access member interface {interface_name}")
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
            "int_port_channel_access_host",
            "int_port_channel_access_member_11_1",
            "int_access_host",
            "int_trunk_host",
            "int_routed_host"
        ]
        
        for policy in policy_order:
            interfaces = updated_interfaces.get(policy, [])
            if not interfaces:
                continue
            
            print(f"[Interface] Updating {len(interfaces)} {policy} interfaces")
            success = interface_api.update_interface(policy, interfaces)
        
        return success
