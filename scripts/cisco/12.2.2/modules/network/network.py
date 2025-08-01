#!/usr/bin/env python3
"""
Network Manager - Unified Network Management Interface

This module provides a clean, unified interface for all network operations with:
- YAML-based network configuration management
- Network CRUD operations with configuration merging
- Template payload generation with field mapping
- Corp defaults integration and Layer 2 Only support
- Network attachment/detachment to switch interfaces
"""

from typing import List, Dict, Any, Tuple, Optional
import json

import api.network as network_api
from modules.config_utils import load_yaml_file, validate_configuration_files
from config.config_factory import config_factory

class NetworkManager:
    """Unified network operations manager with YAML configuration support."""
    
    def __init__(self):
        """Initialize with centralized configuration paths."""
        self.config_paths = config_factory.create_network_config()
        self.switch_config_paths = config_factory.create_switch_config()
        self.defaults_path = self.config_paths['defaults_path']
        self.field_mapping_path = self.config_paths['field_mapping_path']
        self.config_path = self.config_paths['config_path']
        # Initialize network API
        self.network_api = network_api
        # Lazy-loaded cached configurations
        self._defaults = None
        self._field_mapping = None
        self._networks = None
    
    @property
    def defaults(self) -> Dict[str, Any]:
        """Get corp defaults with lazy loading."""
        if self._defaults is None:
            self._defaults = load_yaml_file(str(self.defaults_path))
        return self._defaults
    
    @property
    def field_mapping(self) -> Dict[str, Any]:
        """Get field mapping with lazy loading."""
        if self._field_mapping is None:
            self._field_mapping = load_yaml_file(str(self.field_mapping_path))
        return self._field_mapping
    
    @property
    def networks(self) -> List[Dict[str, Any]]:
        """Get network configurations with lazy loading and caching."""
        if self._networks is None:
            self._load_networks()
        return self._networks
    
    def _load_networks(self) -> None:
        """Load network configurations from YAML file."""
        try:
            config_data = load_yaml_file(str(self.config_path))
            self._networks = config_data.get('Network', [])
        except Exception as e:
            print(f"Error loading network configuration: {e}")
            self._networks = []
    
    def _get_network(self, fabric_name: str, network_name: str) -> Optional[Dict[str, Any]]:
        """Find network by fabric and name."""
        return next(
            (net for net in self.networks 
             if net.get('Fabric') == fabric_name and net.get('Network Name') == network_name),
            None
        )
    
    def _get_effective_vrf(self, network: Dict[str, Any]) -> str:
        """Return VRF name, 'NA' if Layer 2 Only."""
        return "NA" if network.get('Layer 2 Only', False) else network.get('VRF Name', '')
    
    def _validate_resources(self) -> None:
        """Validate required resource files exist."""
        validate_configuration_files([str(self.defaults_path), str(self.field_mapping_path)])
    
    def _build_network_template_config(self, fabric_name: str, network_name: str, network: Dict[str, Any]) -> Dict[str, Any]:
        """Build network template configuration dictionary."""
        # Extract required fields from network data
        vlan_name = network.get('VLAN Name', '')
        vlan_id = str(network.get('VLAN ID', 0))
        intf_description = network.get('Interface Description', '')
        segment_id = str(network.get('Network ID', 0))
        vrf_name = self._get_effective_vrf(network)
        is_layer2_only = "true" if network.get('Layer 2 Only', False) else "false"
        
        # Apply transformations - build base template config
        template_config = {
            "networkName": network_name,
            "vlanName": vlan_name,
            "vlanId": vlan_id,
            "intfDescription": intf_description,
            "segmentId": segment_id,
            "type": "Normal",
            "vrfName": vrf_name,
            "isLayer2Only": is_layer2_only,
            # Required fields with defaults
            "gatewayIpAddress": "",
            "nveId": "1",
            "tag": "12345",
            "mcastGroup": "",
            "switchRole": "",
            "gen_address": "",
            "isIpDhcpRelay": "",
            "flagSet": "",
            "vrfDhcp": "",
            "dhcpServerAddr1": "",
            "dhcpServerAddr2": "",
            "dhcpServerAddr3": "",
            "gen_mask": "",
            "isIp6DhcpRelay": "",
            "dhcpServers": ""
        }
        
        # Apply corp defaults with field mapping
        self._apply_template_defaults(template_config)
        
        # Add gateway for Layer 3 networks
        gateway = network.get('IPv4 Gateway/NetMask', '')
        if gateway and not network.get('Layer 2 Only', False):
            template_config["gatewayIpAddress"] = gateway
        
        return template_config
    
    def _apply_template_defaults(self, template_config: Dict[str, Any]) -> None:
        """Apply corp defaults with field mapping to template config."""
        for section in ["General Parameters", "Advanced"]:
            if section in self.defaults:
                for key, value in self.defaults[section].items():
                    mapped_field = self.field_mapping.get(section, {}).get(key, key)
                    if mapped_field in template_config:
                        template_config[mapped_field] = value
    
    def _build_network_payload(self, fabric_name: str, network_name: str, network: Dict[str, Any]) -> Dict[str, Any]:
        """Build network payload dictionary."""
        # Extract required fields from network data
        network_id = network.get('Network ID', 0)
        vrf_name = self._get_effective_vrf(network)
        vlan_name = network.get('VLAN Name', '')
        
        # Apply transformations - build base payload
        payload = {
            "fabric": fabric_name,
            "networkName": network_name,
            "displayName": network_name,
            "networkId": network_id,
            "networkTemplate": self.defaults.get("networkTemplate", "Default_Network_Universal"),
            "networkExtensionTemplate": self.defaults.get("networkExtensionTemplate", "Default_Network_Extension_Universal"),
            "vrf": vrf_name,
            "vlanName": vlan_name,
            "type": "Normal",
            "hierarchicalKey": fabric_name,
            # Additional fields for complete payload
            "networkTemplateConfig": "",
            "tenantName": None,
            "serviceNetworkTemplate": None,
            "source": None,
            "interfaceGroups": None,
            "primaryNetworkId": -1,
            "primaryNetworkName": None,
            "vlanId": None
        }
        
        return payload

    def _build_complete_payload(self, fabric_name: str, network_name: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Build complete network payload for API operations."""
        self._validate_resources()
        
        network = self._get_network(fabric_name, network_name)
        if not network:
            raise ValueError(f"Network '{network_name}' not found in fabric '{fabric_name}'")
        
        # Build network payload using dictionary approach
        payload = self._build_network_payload(fabric_name, network_name, network)
        
        # Build template config using dictionary approach
        template_config = self._build_network_template_config(fabric_name, network_name, network)
        
        # Return both payload and template config as dictionaries
        # The API layer will handle JSON encoding
        return payload, template_config
    
    # --- Network CRUD Operations ---
    
    def create_network(self, fabric_name: str, network_name: str) -> bool:
        """Create a network using YAML configuration."""
        print(f"[Network] Creating network: {network_name} in fabric: {fabric_name}")
        payload, template_config = self._build_complete_payload(fabric_name, network_name)
        return network_api.create_network(fabric_name, payload, template_config)
    
    def update_network(self, fabric_name: str, network_name: str) -> bool:
        """Update a network using YAML configuration."""
        print(f"[Network] Updating network: {network_name} in fabric: {fabric_name}")
        payload, template_config = self._build_complete_payload(fabric_name, network_name)
        return network_api.update_network(fabric_name, payload, template_config)

    
    def delete_network(self, fabric_name: str, network_name: str) -> bool:
        """Delete a network."""
        print(f"[Network] Deleting network: {network_name} in fabric: {fabric_name}")
        return network_api.delete_network(fabric_name, network_name)
    
    # --- Network Attachment Operations ---
    
    def attach_networks(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Attach networks to switch interfaces based on YAML configuration."""
        print(f"[Network] Attaching networks to switch: {switch_name} in fabric: {fabric_name}, role: {role}")
        
        try:
            # Load and validate switch configuration
            switch_path = self.switch_config_paths['configs_dir'] / fabric_name / role / f"{switch_name}.yaml"
            if not switch_path.exists():
                print(f"[Network] Switch configuration not found: {switch_path}")
                return False
            
            switch_config = load_yaml_file(str(switch_path))
            if not switch_config:
                return False
            
            if not switch_config.get('Serial Number'):
                print(f"[Network] Error: Serial Number not found in switch configuration")
                return False
            
            if 'Interface' not in switch_config:
                print("[Network] No interfaces found to process")
                return True  # No interfaces to process is considered success
            
            # Build network lookup table for the fabric
            network_lookup = {
                net.get('VLAN ID'): {
                    'network_name': net.get('Network Name'),
                    'vlan_id': net.get('VLAN ID')
                }
                for net in self.networks 
                if net.get('Fabric') == fabric_name and net.get('VLAN ID')
            }
            
            serial_number = switch_config.get('Serial Number')
            overall_success = True
            
            # Process all interfaces
            for interface_config in switch_config['Interface']:
                for interface_name, interface_data in interface_config.items():
                    success = self._process_interface(
                        interface_name, interface_data, network_lookup, 
                        'attach', fabric_name, serial_number
                    )
                    if not success:
                        overall_success = False
            
            return overall_success
            
        except Exception as e:
            print(f"[Network] Error attaching networks: {e}")
            return False
    
    def detach_networks(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Detach networks from switch interfaces based on YAML configuration."""
        print(f"[Network] Detaching networks from switch: {switch_name} in fabric: {fabric_name}, role: {role}")
        
        try:
            # Load and validate switch configuration
            switch_path = self.switch_config_paths['configs_dir'] / fabric_name / role / f"{switch_name}.yaml"
            if not switch_path.exists():
                print(f"[Network] Switch configuration not found: {switch_path}")
                return False
            
            switch_config = load_yaml_file(str(switch_path))
            if not switch_config:
                return False
            
            if not switch_config.get('Serial Number'):
                print(f"[Network] Error: Serial Number not found in switch configuration")
                return False
            
            if 'Interface' not in switch_config:
                print("[Network] No interfaces found to process")
                return True  # No interfaces to process is considered success
            
            # Build network lookup table for the fabric
            network_lookup = {
                net.get('VLAN ID'): {
                    'network_name': net.get('Network Name'),
                    'vlan_id': net.get('VLAN ID')
                }
                for net in self.networks 
                if net.get('Fabric') == fabric_name and net.get('VLAN ID')
            }
            
            serial_number = switch_config.get('Serial Number')
            overall_success = True
            
            # Process all interfaces
            for interface_config in switch_config['Interface']:
                for interface_name, interface_data in interface_config.items():
                    success = self._process_interface(
                        interface_name, interface_data, network_lookup, 
                        'detach', fabric_name, serial_number
                    )
                    if not success:
                        overall_success = False
            
            return overall_success
            
        except Exception as e:
            print(f"[Network] Error detaching networks: {e}")
            return False
    
    def _process_interface(self, interface_name: str, interface_data: Dict[str, Any], 
                          network_lookup: Dict[int, Dict[str, Any]], operation: str, 
                          fabric_name: str, serial_number: str) -> bool:
        """Process a single interface based on its policy."""
        policy = interface_data.get('policy')
        
        if policy == 'int_access_host':
            # Process access interface
            access_vlan = interface_data.get('Access Vlan')
            if not access_vlan:
                return True  # No VLAN configured is not an error
            
            try:
                vlan_id = int(access_vlan)
                network_info = network_lookup.get(vlan_id)
                if not network_info:
                    return True  # Network not found in lookup is not an error
                
                network_name = network_info['network_name']
                
                if operation == 'attach':
                    result = self.network_api.attach_network(
                        fabric_name, network_name, serial_number, interface_name, vlan_id
                    )
                else:  # detach
                    result = self.network_api.detach_network(
                        fabric_name, network_name, serial_number, interface_name, vlan_id
                    )
                
                if result:
                    print(f"[Network] Successfully {operation}ed network {network_name} (VLAN {vlan_id}) "
                          f"to interface {interface_name}")
                else:
                    print(f"[Network] Failed to {operation} network {network_name} (VLAN {vlan_id}) "
                          f"to interface {interface_name}")
                
                return result
            except ValueError:
                print(f"[Network] Invalid VLAN ID '{access_vlan}' for interface {interface_name}")
                return False
        
        elif policy == 'int_trunk_host':
            # Process trunk interface
            trunk_vlans = interface_data.get('Trunk Allowed Vlans')
            
            # If no VLANs specified, stop
            if not trunk_vlans:
                return True
            try:
                # Parse trunk VLAN string into list of VLAN IDs
                vlan_ids = [int(vlan.strip()) for vlan in str(trunk_vlans).split(',') 
                           if vlan.strip() and vlan.strip().isdigit()]
                
                # Process each VLAN
                for vlan_id in vlan_ids:
                    if vlan_id not in network_lookup:
                        print(f"[Network] Warning: Network for VLAN {vlan_id} not found in fabric {fabric_name}")
                        continue
                    
                    network_info = network_lookup[vlan_id]
                    network_name = network_info['network_name']
                    
                    try:
                        if operation == "attach":
                            result = self.network_api.attach_network(
                                fabric_name, network_name, serial_number, interface_name, vlan_id
                            )
                        else:  # detach
                            result = self.network_api.detach_network(
                                fabric_name, network_name, serial_number, interface_name, vlan_id
                            )
                        
                        if result:
                            print(f"[Network] Successfully {operation}ed network {network_name} (VLAN {vlan_id}) "
                                  f"to interface {interface_name}")
                        else:
                            print(f"[Network] Failed to {operation} network {network_name} (VLAN {vlan_id}) "
                                  f"to interface {interface_name}")
                            return False
                    except Exception as e:
                        print(f"[Network] Error during {operation} operation for VLAN {vlan_id}: {e}")
                        return False
                
                return True
            except ValueError as e:
                print(f"[Network] Error parsing trunk VLANs for {interface_name}: {e}")
                return False
        
        return True  # Unknown policy types are skipped but not considered failure
