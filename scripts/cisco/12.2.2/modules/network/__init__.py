#!/usr/bin/env python3
"""
Network Management Module - Core Components

This module provides the core functionality for building and managing Networks:
- Network Creation, Update, and Deletion
- Network Template Configuration Management
- Network payload generation and field mapping

It handles configuration merging, field mapping, and API payload generation
for Cisco NDFC Network management.
"""

import os
import sys
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Update import path to go back to parent directory for api and modules
sys.path.append(str(Path(__file__).parent.parent.absolute()))
import api.network as network_api
from modules.config_utils import (
    load_yaml_file, merge_configs, 
    apply_field_mapping, get_nested_value,
    validate_file_exists, 
    validate_configuration_files, flatten_config
)
from modules.common_utils import MessageFormatter, setup_module_path

# --- Constants and Enums ---

class NetworkTemplate(Enum):
    """Enumeration of supported Network templates."""
    DEFAULT_NETWORK_UNIVERSAL = "Default_Network_Universal"
    DEFAULT_NETWORK_EXTENSION_UNIVERSAL = "Default_Network_Extension_Universal"

@dataclass
class NetworkConfig:
    """Configuration paths and parameters for Network building."""
    config_path: str
    defaults_path: str
    field_mapping_path: str

@dataclass
class NetworkEntry:
    """Individual network configuration entry."""
    fabric: str
    network_name: str
    layer2_only: bool
    vrf_name: str
    network_id: int
    vlan_id: int
    gateway_netmask: str
    vlan_name: str
    interface_description: str

# --- Configuration Loading and Validation ---

def load_network_configuration() -> List[NetworkEntry]:
    """
    Load network configuration from the 5_segment/network.yaml file.
    
    Returns:
        List[NetworkEntry]: List of network configurations
    """
    config_path = "c:/Users/TNDO-ADMIN/Desktop/Repo_fabric/network_configs/5_segment/network.yaml"
    
    try:
        config_data = load_yaml_file(config_path)
        networks = []
        
        for network_config in config_data.get('Network', []):
            networks.append(NetworkEntry(
                fabric=network_config.get('Fabric', ''),
                network_name=network_config.get('Network Name', ''),
                layer2_only=network_config.get('Layer 2 Only', False),
                vrf_name=network_config.get('VRF Name', ''),
                network_id=network_config.get('Network ID', 0),
                vlan_id=network_config.get('VLAN ID', 0),
                gateway_netmask=network_config.get('IPv4 Gateway/NetMask', ''),
                vlan_name=network_config.get('VLAN Name', ''),
                interface_description=network_config.get('Interface Description', '')
            ))
        
        return networks
        
    except Exception as e:
        print(f"Error loading network configuration: {e}")
        return []

def get_network_by_name(fabric_name: str, network_name: str) -> Optional[NetworkEntry]:
    """
    Get a specific network configuration by fabric and network name.
    
    Args:
        fabric_name: Name of the fabric
        network_name: Name of the network
        
    Returns:
        NetworkEntry or None if not found
    """
    networks = load_network_configuration()
    for network in networks:
        if network.fabric == fabric_name and network.network_name == network_name:
            return network
    return None

# --- Resource Loading ---

def get_network_resources() -> NetworkConfig:
    """Get the paths to network configuration resources."""
    base_path = str(Path(__file__).parent.parent.parent / "resources")
    
    return NetworkConfig(
        config_path="",  # Will be populated from 5_segment/network.yaml
        defaults_path=os.path.join(base_path, "corp_defaults", "network.yaml"),
        field_mapping_path=os.path.join(base_path, "_field_mapping", "network.yaml")
    )

# --- Core Builder Classes ---

class NetworkBuilder:
    """
    Main class for building network configurations from YAML.
    """
    
    def __init__(self):
        """Initialize the NetworkBuilder with resource paths."""
        self.config = get_network_resources()
        self.message_formatter = MessageFormatter()
        
    def _validate_resources(self):
        """Validate that all required resource files exist."""
        files_to_check = [
            self.config.defaults_path,
            self.config.field_mapping_path
        ]
        
        validate_configuration_files(files_to_check)
    
    def build_network_config(self, fabric_name: str, network_name: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Build network configuration from YAML files.
        
        Args:
            fabric_name: Name of the fabric
            network_name: Name of the network
            
        Returns:
            Tuple containing (network_payload, template_payload)
        """
        self._validate_resources()
        
        # Get network configuration from 5_segment/network.yaml
        network_entry = get_network_by_name(fabric_name, network_name)
        if not network_entry:
            raise ValueError(f"Network '{network_name}' not found in fabric '{fabric_name}'")
        
        # Load defaults and field mapping
        defaults = load_yaml_file(self.config.defaults_path)
        field_mapping = load_yaml_file(self.config.field_mapping_path)
        
        # Create network payload generator
        payload_generator = NetworkPayloadGenerator(defaults, field_mapping)
        
        # Generate payloads
        network_payload = payload_generator.generate_network_payload(network_entry)
        template_payload = payload_generator.generate_template_payload(network_entry, defaults)
        
        return network_payload, template_payload

class NetworkPayloadGenerator:
    """
    Generates API payloads for network operations.
    """
    
    def __init__(self, defaults: Dict[str, Any], field_mapping: Dict[str, Any]):
        """
        Initialize with defaults and field mapping.
        
        Args:
            defaults: Default configuration values
            field_mapping: Field mapping configuration
        """
        self.defaults = defaults
        self.field_mapping = field_mapping
    
    def generate_network_payload(self, network_entry: NetworkEntry) -> Dict[str, Any]:
        """
        Generate the main network payload.
        
        Args:
            network_entry: Network configuration entry
            
        Returns:
            Dict containing the network payload
        """
        # Set VRF name to "NA" if Layer 2 Only is true
        vrf_name = "NA" if network_entry.layer2_only else network_entry.vrf_name
        
        return {
            "fabric": network_entry.fabric,
            "networkName": network_entry.network_name,
            "displayName": network_entry.network_name,
            "networkId": network_entry.network_id,
            "networkTemplate": self.defaults.get("networkTemplate", "Default_Network_Universal"),
            "networkExtensionTemplate": self.defaults.get("networkExtensionTemplate", "Default_Network_Extension_Universal"),
            "vrf": vrf_name,
            "vlanName": network_entry.vlan_name,
            "type": "Normal"
        }
    
    def generate_template_payload(self, network_entry: NetworkEntry, defaults: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate the network template configuration payload.
        
        Args:
            network_entry: Network configuration entry
            defaults: Default configuration values
            
        Returns:
            Dict containing the template payload
        """
        template_payload = {}
        
        # Apply default values from corp_defaults
        if "General Parameters" in defaults:
            for key, default_value in defaults["General Parameters"].items():
                mapped_field = self.field_mapping.get("General Parameters", {}).get(key, key)
                template_payload[mapped_field] = default_value
        
        if "Advanced" in defaults:
            for key, default_value in defaults["Advanced"].items():
                mapped_field = self.field_mapping.get("Advanced", {}).get(key, key)
                template_payload[mapped_field] = default_value
        
        # Override with specific network values
        template_payload["networkName"] = network_entry.network_name
        template_payload["vlanName"] = network_entry.vlan_name
        template_payload["vlanId"] = str(network_entry.vlan_id)
        template_payload["intfDescription"] = network_entry.interface_description
        template_payload["segmentId"] = str(network_entry.network_id)
        template_payload["type"] = "Normal"
        
        # Set VRF name - "NA" if Layer 2 Only is true
        if network_entry.layer2_only:
            template_payload["vrfName"] = "NA"
            template_payload["isLayer2Only"] = "true"
        else:
            template_payload["vrfName"] = network_entry.vrf_name
            template_payload["isLayer2Only"] = "false"
        
        # Set gateway if provided and not Layer 2 Only
        if network_entry.gateway_netmask and not network_entry.layer2_only:
            template_payload["gatewayIpAddress"] = network_entry.gateway_netmask
        
        # Set default values for required fields that might not be in defaults
        template_payload.setdefault("nveId", "1")
        template_payload.setdefault("tag", "12345")
        template_payload.setdefault("mcastGroup", "")
        template_payload.setdefault("switchRole", "")
        template_payload.setdefault("gen_address", "")
        template_payload.setdefault("isIpDhcpRelay", "")
        template_payload.setdefault("flagSet", "")
        template_payload.setdefault("dhcpServerAddr1", "")
        template_payload.setdefault("dhcpServerAddr2", "")
        template_payload.setdefault("dhcpServerAddr3", "")
        template_payload.setdefault("vrfDhcp", "")
        template_payload.setdefault("gen_mask", "")
        template_payload.setdefault("isIp6DhcpRelay", "")
        template_payload.setdefault("dhcpServers", "")
        
        return template_payload

# --- Operation Functions ---

def create_network(fabric_name: str, network_name: str) -> bool:
    """
    Create a network using YAML configuration.
    
    Args:
        fabric_name: Name of the fabric
        network_name: Name of the network
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        builder = NetworkBuilder()
        
        # Build configuration
        network_payload, template_payload = builder.build_network_config(fabric_name, network_name)

        # Execute creation
        success = network_api.create_network(fabric_name, network_payload, template_payload)
        
        return success
        
    except Exception as e:
        print(f"Error creating network: {e}")
        return False

def update_network(fabric_name: str, network_name: str) -> bool:
    """
    Update a network using YAML configuration.
    
    Args:
        fabric_name: Name of the fabric
        network_name: Name of the network
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        builder = NetworkBuilder()
        
        # Build configuration
        network_payload, template_payload = builder.build_network_config(fabric_name, network_name)
        
        # Execute update
        success = network_api.update_network(fabric_name, network_payload, template_payload)
        
        return success
        
    except Exception as e:
        print(f"Error updating network: {e}")
        return False

def delete_network(fabric_name: str, network_name: str) -> bool:
    """
    Delete a network.
    
    Args:
        fabric_name: Name of the fabric
        network_name: Name of the network
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Execute deletion
        success = network_api.delete_network(fabric_name, network_name)
        
        return success
        
    except Exception as e:
        print(f"Error deleting network: {e}")
        return False
