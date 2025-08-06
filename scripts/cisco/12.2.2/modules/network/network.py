#!/usr/bin/env python3
"""
Network Manager - Unified Network Management Interface

This module provides a clean, unified interface for all network operations with:
- YAML-based network configuration management
- Network CRUD operations with configuration merging
- Template payload generation with field mapping
- Corp defaults integration and Layer 2 Only support
- Network attachment/detachment to switches (reads switch config for serial number, no interface parsing)
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
            print(f"[Network] Loading network config from: {self.config_path}")
            config_data = load_yaml_file(str(self.config_path))
            self._networks = config_data.get('Network', [])
        except Exception as e:
            print(f"Error loading network configuration: {e}")
            self._networks = []
    
    def _get_network(self, network_name: str) -> Optional[Dict[str, Any]]:
        """Find network by name regardless of fabric."""
        for net in self.networks:
            if net.get('Network Name') == network_name:
                return net
        return None
    
    def _get_effective_vrf(self, network: Dict[str, Any]) -> str:
        """Return VRF name, 'NA' if Layer 2 Only."""
        return "NA" if network.get('Layer 2 Only', False) else network.get('VRF Name', '')
    
    def _validate_resources(self) -> None:
        """Validate required resource files exist."""
        validate_configuration_files([str(self.defaults_path), str(self.field_mapping_path)])
    
    def _build_network_template_config(self, network_name: str, network: Dict[str, Any]) -> Dict[str, Any]:
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
        
        network = self._get_network(network_name)
        if not network:
            raise ValueError(f"Network '{network_name}' not found in configuration")
        
        # Build network payload using dictionary approach
        payload = self._build_network_payload(fabric_name, network_name, network)
        
        # Build template config using dictionary approach
        template_config = self._build_network_template_config(network_name, network)

        # Return both payload and template config as dictionaries
        # The API layer will handle JSON encoding
        return payload, template_config
    
    # --- Network CRUD Operations ---
    
    def sync(self, fabric_name: str) -> bool:
        """Update all networks for a fabric - delete unwanted, update existing, and create missing networks."""
        print(f"[Network] Updating all networks in fabric '{fabric_name}'")
        
        try:
            # Get existing networks from the fabric
            existing_networks = network_api.get_networks(fabric_name)
            existing_network_names = {net.get('networkName') for net in existing_networks}
            print(f"[Network] Found {len(existing_network_names)} existing networks: {existing_network_names}")
            
            # Get networks from YAML config for this fabric
            fabric_networks = [net for net in self.networks if net.get('Fabric') == fabric_name]
            yaml_network_names = {net.get('Network Name') for net in fabric_networks}
            print(f"[Network] Found {len(yaml_network_names)} networks in YAML: {yaml_network_names}")
            
            # Find networks to delete (exist in fabric but not in YAML)
            networks_to_delete = existing_network_names - yaml_network_names
            print(f"[Network] Networks to delete: {networks_to_delete}")
            
            # Find networks to create (exist in YAML but not in fabric)
            networks_to_create = yaml_network_names - existing_network_names
            print(f"[Network] Networks to create: {networks_to_create}")
            
            # Find networks to update (exist in both fabric and YAML)
            networks_to_update = existing_network_names.intersection(yaml_network_names)
            print(f"[Network] Networks to update: {networks_to_update}")
            
            overall_success = True
            
            # Delete unwanted networks
            for network_name in networks_to_delete:
                success = self.delete_network(fabric_name, network_name)
                if not success:
                    overall_success = False
    
            # Update existing networks
            for network_name in networks_to_update:
                success = self.update_network(fabric_name, network_name)
                if not success:
                    overall_success = False

            # Create missing networks
            for network_name in networks_to_create:
                success = self.create_network(fabric_name, network_name)
                if not success:
                    overall_success = False

            if overall_success:
                print(f"[Network] Successfully updated all networks for fabric '{fabric_name}'")

            return overall_success
            
        except Exception as e:
            print(f"[Network] Error updating networks: {e}")
            return False
    
    def create_network(self, fabric_name: str, network_name: str) -> bool:
        """Create a network using YAML configuration."""
        print(f"[Network] Creating network '{network_name}' in fabric '{fabric_name}'")
        
        try:
            # Check if network already exists
            existing_networks = network_api.get_networks(fabric_name)
            existing_network_names = {net.get('networkName') for net in existing_networks}
            
            if network_name in existing_network_names:
                print(f"[Network] Network '{network_name}' already exists in fabric '{fabric_name}', skipping creation")
                return True
            
            payload, template_config = self._build_complete_payload(fabric_name, network_name)
            return network_api.create_network(fabric_name, payload, template_config)
            
        except Exception as e:
            print(f"[Network] Error creating network '{network_name}': {e}")
            return False
    
    def update_network(self, fabric_name: str, network_name: str) -> bool:
        """Update a network using YAML configuration."""
        print(f"[Network] Updating network '{network_name}' in fabric '{fabric_name}'")
        payload, template_config = self._build_complete_payload(fabric_name, network_name)
        return network_api.update_network(fabric_name, payload, template_config)

    
    def delete_network(self, fabric_name: str, network_name: str) -> bool:
        """Delete a network."""
        print(f"[Network] Deleting network '{network_name}' in fabric '{fabric_name}'")
        return network_api.delete_network(fabric_name, network_name)
    
    # --- Network Attachment Operations ---
    
    def attach_networks(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Attach all networks to a device based on YAML configuration."""
        print(f"[Network] Attaching networks to switch '{switch_name}' ({role}) in fabric '{fabric_name}'")

        try:
            # Load switch configuration to get serial number and IP
            switch_path = self.switch_config_paths['configs_dir'] / fabric_name / role / f"{switch_name}.yaml"
            print(f"[Network] Loading switch config from: {switch_path}")
            if not switch_path.exists():
                print(f"[Network] Switch configuration not found: {switch_path}")
                return False
            
            switch_config = load_yaml_file(str(switch_path))
            if not switch_config:
                return False
            
            serial_number = switch_config.get('Serial Number')
            switch_ip = switch_config.get('IP Address')
            
            if not serial_number:
                print(f"[Network] Error: Serial Number not found in switch configuration")
                return False
            
            if not switch_ip:
                print(f"[Network] Error: IP Address not found in switch configuration")
                return False
            
            # Get all networks for the specified fabric
            fabric_networks = [net for net in self.networks if net.get('Fabric') == fabric_name]
            
            if not fabric_networks:
                print(f"[Network] No networks found for fabric '{fabric_name}'")
                return True  # No networks to process is considered success
            
            # Build payload for all networks
            payload = []
            for network in fabric_networks:
                network_name = network.get('Network Name')
                
                if network_name:
                    network_payload = {
                        "networkName": network_name,
                        "switchName": switch_name,
                        "switchIP": switch_ip,
                        "switchSN": serial_number,
                        "peerSwitchSN": None,
                        "peerSwitchName": None,
                        "ports": "",
                        "torSwitches": None,
                        "allSwitches": [switch_name]
                    }
                    payload.append(network_payload)
                    print(f"[Network] Added network '{network_name}' to attach payload")
                else:
                    print(f"[Network] Skipping network with missing name: {network}")
            
            if not payload:
                print(f"[Network] No valid networks to attach")
                return True
            
            # Call API with complete payload
            result = network_api.attach_network(payload)
            return result
            
        except Exception as e:
            print(f"[Network] Error attaching networks: {e}")
            return False
    
    def detach_networks(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Detach all networks from a device based on YAML configuration."""
        print(f"[Network] Detaching networks from switch '{switch_name}' ({role}) in fabric '{fabric_name}'")

        try:
            # Load switch configuration to get serial number and IP
            switch_path = self.switch_config_paths['configs_dir'] / fabric_name / role / f"{switch_name}.yaml"
            print(f"[Network] Loading switch config from: {switch_path}")
            if not switch_path.exists():
                print(f"[Network] Switch configuration not found: {switch_path}")
                return False
            
            switch_config = load_yaml_file(str(switch_path))
            if not switch_config:
                return False
            
            serial_number = switch_config.get('Serial Number')
            switch_ip = switch_config.get('IP Address')
            
            if not serial_number:
                print(f"[Network] Error: Serial Number not found in switch configuration")
                return False
            
            if not switch_ip:
                print(f"[Network] Error: IP Address not found in switch configuration")
                return False
            
            # Get all networks for the specified fabric
            fabric_networks = [net for net in self.networks if net.get('Fabric') == fabric_name]
            
            if not fabric_networks:
                print(f"[Network] No networks found for fabric '{fabric_name}'")
                return True  # No networks to process is considered success
            
            # Build payload for all networks in the new detach format
            payload = []
            for network in fabric_networks:
                network_name = network.get('Network Name')
                vlan_id = network.get('VLAN ID', -1)
                
                if network_name:
                    network_payload = {
                        "networkName": network_name,
                        "lanAttachList": [{
                            "fabric": fabric_name,
                            "networkName": network_name,
                            "serialNumber": serial_number,
                            "vlan": vlan_id,
                            "switchPorts": "",
                            "detachSwitchPorts": "",
                            "dot1QVlan": 1,
                            "untagged": False,
                            "freeformConfig": "",
                            "deployment": False,
                            "extensionValues": "",
                            "instanceValues": ""
                        }]
                    }
                    payload.append(network_payload)
                    print(f"[Network] Added network '{network_name}' to detach payload")
                else:
                    print(f"[Network] Skipping network with missing name: {network}")
            
            if not payload:
                print(f"[Network] No valid networks to detach")
                return True
            
            # Call API with complete payload
            result = network_api.detach_network(fabric_name, payload)
            return result
            
        except Exception as e:
            print(f"[Network] Error detaching networks: {e}")
            return False
