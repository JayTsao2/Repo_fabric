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
from dataclasses import dataclass, asdict
import json

import api.network as network_api
from modules.config_utils import load_yaml_file, validate_configuration_files
from config.config_factory import config_factory

@dataclass
class NetworkTemplateConfig:
    """Network template configuration with all required fields."""
    # Core network fields
    networkName: str
    vlanName: str
    vlanId: str
    intfDescription: str
    segmentId: str
    type: str
    vrfName: str
    isLayer2Only: str
    
    # Optional gateway
    gatewayIpAddress: str = ""
    
    # Required fields with defaults
    nveId: str = "1"
    tag: str = "12345"
    mcastGroup: str = ""
    switchRole: str = ""
    gen_address: str = ""
    isIpDhcpRelay: str = ""
    flagSet: str = ""
    vrfDhcp: str = ""
    dhcpServerAddr1: str = ""
    dhcpServerAddr2: str = ""
    dhcpServerAddr3: str = ""
    gen_mask: str = ""
    isIp6DhcpRelay: str = ""
    dhcpServers: str = ""
    
    def to_json(self) -> str:
        """Convert to JSON string for API payload."""
        return json.dumps(asdict(self))
    
    def apply_defaults(self, defaults: Dict[str, Any], field_mapping: Dict[str, Any]) -> None:
        """Apply corp defaults with field mapping."""
        for section in ["General Parameters", "Advanced"]:
            if section in defaults:
                for key, value in defaults[section].items():
                    mapped_field = field_mapping.get(section, {}).get(key, key)
                    if hasattr(self, mapped_field):
                        setattr(self, mapped_field, value)

@dataclass
class NetworkPayload:
    """Network payload structure for API operations."""
    fabric: str
    networkName: str
    displayName: str
    networkId: int
    networkTemplate: str
    networkExtensionTemplate: str
    vrf: str
    vlanName: str
    type: str
    
    # Additional fields for complete payload
    networkTemplateConfig: str = ""
    tenantName: Optional[str] = None
    serviceNetworkTemplate: Optional[str] = None
    source: Optional[str] = None
    interfaceGroups: Optional[str] = None
    primaryNetworkId: int = -1
    primaryNetworkName: Optional[str] = None
    vlanId: Optional[int] = None
    hierarchicalKey: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls."""
        return asdict(self)

class NetworkManager:
    """Unified network operations manager with YAML configuration support."""
    
    def __init__(self):
        """Initialize with centralized configuration paths."""
        self.config_paths = config_factory.create_network_config()
        self.defaults_path = self.config_paths['defaults_path']
        self.field_mapping_path = self.config_paths['field_mapping_path']
        self.config_path = self.config_paths['config_path']
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
    
    def _build_complete_payload(self, fabric_name: str, network_name: str) -> Tuple[Dict[str, Any], str]:
        """Build complete network payload for API operations."""
        self._validate_resources()
        
        network = self._get_network(fabric_name, network_name)
        if not network:
            raise ValueError(f"Network '{network_name}' not found in fabric '{fabric_name}'")
        
        # Build NetworkPayload dataclass
        payload = NetworkPayload(
            fabric=fabric_name,
            networkName=network_name,
            displayName=network_name,
            networkId=network.get('Network ID', 0),
            networkTemplate=self.defaults.get("networkTemplate", "Default_Network_Universal"),
            networkExtensionTemplate=self.defaults.get("networkExtensionTemplate", "Default_Network_Extension_Universal"),
            vrf=self._get_effective_vrf(network),
            vlanName=network.get('VLAN Name', ''),
            type="Normal",
            hierarchicalKey=fabric_name
        )
        
        # Build NetworkTemplateConfig dataclass
        template_config = NetworkTemplateConfig(
            networkName=network_name,
            vlanName=network.get('VLAN Name', ''),
            vlanId=str(network.get('VLAN ID', 0)),
            intfDescription=network.get('Interface Description', ''),
            segmentId=str(network.get('Network ID', 0)),
            type="Normal",
            vrfName=self._get_effective_vrf(network),
            isLayer2Only="true" if network.get('Layer 2 Only', False) else "false"
        )
        
        # Apply corp defaults with field mapping
        template_config.apply_defaults(self.defaults, self.field_mapping)
        
        # Add gateway for Layer 3 networks
        gateway = network.get('IPv4 Gateway/NetMask', '')
        if gateway and not network.get('Layer 2 Only', False):
            template_config.gatewayIpAddress = gateway
        
        # Convert template config to JSON string
        template_config_json = template_config.to_json()
        payload.networkTemplateConfig = template_config_json
        
        return payload.to_dict(), template_config_json
    
    # --- Network CRUD Operations ---
    
    def create_network(self, fabric_name: str, network_name: str) -> bool:
        """Create a network using YAML configuration."""
        try:
            print(f"[Network] Creating network: {network_name} in fabric: {fabric_name}")
            payload, template_config = self._build_complete_payload(fabric_name, network_name)
            return network_api.create_network(fabric_name, payload, template_config)
        except Exception as e:
            print(f"Error creating network: {e}")
            return False
    
    def update_network(self, fabric_name: str, network_name: str) -> bool:
        """Update a network using YAML configuration."""
        try:
            print(f"[Network] Updating network: {network_name} in fabric: {fabric_name}")
            payload, template_config = self._build_complete_payload(fabric_name, network_name)
            return network_api.update_network(fabric_name, payload, template_config)
        except Exception as e:
            print(f"Error updating network: {e}")
            return False
    
    def delete_network(self, fabric_name: str, network_name: str) -> bool:
        """Delete a network."""
        try:
            print(f"[Network] Deleting network: {network_name} in fabric: {fabric_name}")
            return network_api.delete_network(fabric_name, network_name)
        except Exception as e:
            print(f"Error deleting network: {e}")
            return False
    
    # --- Network Attachment Operations ---
    
    def attach_networks(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Attach networks to switch interfaces based on YAML configuration."""
        print(f"[Network] Attaching networks to switch: {switch_name} in fabric: {fabric_name}, role: {role}")
        return self._process_switch_networks(fabric_name, role, switch_name, 'attach')
    
    def detach_networks(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Detach networks from switch interfaces based on YAML configuration."""
        print(f"[Network] Detaching networks from switch: {switch_name} in fabric: {fabric_name}, role: {role}")
        return self._process_switch_networks(fabric_name, role, switch_name, 'detach')
    
    def _process_switch_networks(self, fabric_name: str, role: str, switch_name: str, operation: str) -> bool:
        """Process network attach/detach operations for a switch."""
        try:
            print(f"{operation.capitalize()}ing networks {'to' if operation == 'attach' else 'from'} {switch_name} ({role}) in {fabric_name}...")
            
            # Load switch configuration
            switch_path = self.config_paths['configs_dir'] / fabric_name / role / f"{switch_name}.yaml"
            if not switch_path.exists():
                print(f"Switch configuration not found: {switch_path}")
                return False
            
            switch_config = load_yaml_file(str(switch_path))
            if 'Interface' not in switch_config:
                print("No interfaces found to process")
                return True
            
            # Create network lookup for this fabric
            network_lookup = {
                net.get('VLAN ID'): net.get('Network Name')
                for net in self.networks 
                if net.get('Fabric') == fabric_name and net.get('VLAN ID')
            }
            
            api_func = getattr(network_api, f"{operation}_network")
            success = True
            processed_count = 0
            
            # Process all interfaces
            for interface_config in switch_config['Interface']:
                for interface_name, interface_data in interface_config.items():
                    policy = interface_data.get('policy')
                    
                    if policy == 'int_access_host':
                        access_vlan = interface_data.get('Access Vlan')
                        if access_vlan:
                            try:
                                vlan_id = int(access_vlan)
                                if vlan_id in network_lookup:
                                    network_name = network_lookup[vlan_id]
                                    if api_func(fabric_name, network_name, switch_name, [interface_name]):
                                        print(f"Success: {operation.capitalize()}ed {network_name} {'to' if operation == 'attach' else 'from'} {interface_name} (ACCESS)")
                                        processed_count += 1
                                    else:
                                        print(f"Failed to {operation} {network_name} {'to' if operation == 'attach' else 'from'} {interface_name}")
                                        success = False
                            except ValueError:
                                print(f"Invalid VLAN ID '{access_vlan}' for interface {interface_name}")
                    
                    elif policy == 'int_trunk_host':
                        trunk_vlans = interface_data.get('Trunk Allowed Vlans')
                        if trunk_vlans and not (isinstance(trunk_vlans, str) and 
                                              (trunk_vlans.strip() == '' or 'controlled by policy' in trunk_vlans.lower())):
                            try:
                                vlan_ids = [int(vlan.strip()) for vlan in str(trunk_vlans).split(',') 
                                           if vlan.strip() and vlan.strip().isdigit()]
                                
                                for vlan_id in vlan_ids:
                                    if vlan_id in network_lookup:
                                        network_name = network_lookup[vlan_id]
                                        if api_func(fabric_name, network_name, switch_name, [interface_name]):
                                            print(f"Success: {operation.capitalize()}ed {network_name} {'to' if operation == 'attach' else 'from'} {interface_name} (TRUNK)")
                                            processed_count += 1
                                        else:
                                            print(f"Failed to {operation} {network_name} {'to' if operation == 'attach' else 'from'} {interface_name}")
                                            success = False
                            except ValueError as e:
                                print(f"Error parsing trunk VLANs for {interface_name}: {e}")
            
            status = "Success" if success else "Failed"
            print(f"{status}: {operation.capitalize()}ed {processed_count} network interfaces for {switch_name}")
            return success
            
        except Exception as e:
            print(f"Error {operation}ing networks: {e}")
            return False
