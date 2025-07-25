#!/usr/bin/env python3
"""
Network Attachment Module

This module handles the attachment and detachment of networks to/from switch interfaces.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Setup module path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from modules.network import load_network_configuration, get_network_by_name
from modules.config_utils import load_yaml_file
from modules.common_utils import MessageFormatter
import api.network as network_api

class NetworkAttachment:
    """Handles network attachment and detachment operations."""
    
    def __init__(self):
        """Initialize the NetworkAttachment."""
        self.message_formatter = MessageFormatter()
    
    def get_switch_configuration(self, fabric_name: str, role: str, switch_name: str) -> Optional[Dict[str, Any]]:
        """
        Load switch configuration from YAML file.
        
        Args:
            fabric_name: Name of the fabric
            role: Role of the switch (leaf, spine, etc.)
            switch_name: Name of the switch
            
        Returns:
            Dict containing switch configuration or None if not found
        """
        try:
            switch_file_path = f"c:/Users/TNDO-ADMIN/Desktop/Repo_fabric/network_configs/3_node/{fabric_name}/{role}/{switch_name}.yaml"
            if not os.path.exists(switch_file_path):
                print(f"Switch configuration file not found: {switch_file_path}")
                return None
            
            return load_yaml_file(switch_file_path)
            
        except Exception as e:
            print(f"Error loading switch configuration: {e}")
            return None
    
    def parse_access_interfaces(self, switch_config: Dict[str, Any], fabric_name: str) -> List[Dict[str, Any]]:
        """
        Parse interfaces with int_access_host policy and Access Vlan.
        
        Args:
            switch_config: Switch configuration dictionary
            fabric_name: Name of the fabric
            
        Returns:
            List of interface configurations for access ports
        """
        access_interfaces = []
        networks = load_network_configuration()
        
        # Create a lookup dictionary for networks by VLAN ID
        network_lookup = {}
        for network in networks:
            if network.fabric == fabric_name:
                network_lookup[network.vlan_id] = network
        
        if 'Interface' in switch_config:
            for interface_config in switch_config['Interface']:
                for interface_name, interface_data in interface_config.items():
                    policy = interface_data.get('policy')
                    access_vlan = interface_data.get('Access Vlan')
                    
                    if policy == 'int_access_host' and access_vlan:
                        try:
                            vlan_id = int(access_vlan)
                            if vlan_id in network_lookup:
                                network = network_lookup[vlan_id]
                                access_interfaces.append({
                                    'interface_name': interface_name,
                                    'vlan_id': vlan_id,
                                    'network_name': network.network_name,
                                    'network': network
                                })
                        except ValueError:
                            print(f"Invalid VLAN ID '{access_vlan}' for interface {interface_name}")
        
        return access_interfaces
    
    def parse_trunk_interfaces(self, switch_config: Dict[str, Any], fabric_name: str) -> List[Dict[str, Any]]:
        """
        Parse interfaces with int_trunk_host policy and Trunk Allowed Vlans.
        
        Args:
            switch_config: Switch configuration dictionary
            fabric_name: Name of the fabric
            
        Returns:
            List of interface configurations for trunk ports
        """
        trunk_interfaces = []
        networks = load_network_configuration()
        
        # Create a lookup dictionary for networks by VLAN ID
        network_lookup = {}
        for network in networks:
            if network.fabric == fabric_name:
                network_lookup[network.vlan_id] = network
        
        if 'Interface' in switch_config:
            for interface_config in switch_config['Interface']:
                for interface_name, interface_data in interface_config.items():
                    policy = interface_data.get('policy')
                    trunk_vlans = interface_data.get('Trunk Allowed Vlans')
                    
                    if policy == 'int_trunk_host' and trunk_vlans:
                        # Skip if trunk_vlans is blank or controlled by policy
                        if isinstance(trunk_vlans, str) and (trunk_vlans.strip() == '' or 'controlled by policy' in trunk_vlans.lower()):
                            continue
                            
                        try:
                            # Parse comma-separated VLAN IDs
                            vlan_ids = []
                            for vlan_str in str(trunk_vlans).split(','):
                                vlan_str = vlan_str.strip()
                                if vlan_str and vlan_str.isdigit():
                                    vlan_ids.append(int(vlan_str))
                            
                            # Find matching networks for each VLAN
                            interface_networks = []
                            for vlan_id in vlan_ids:
                                if vlan_id in network_lookup:
                                    network = network_lookup[vlan_id]
                                    interface_networks.append({
                                        'vlan_id': vlan_id,
                                        'network_name': network.network_name,
                                        'network': network
                                    })
                            
                            if interface_networks:
                                trunk_interfaces.append({
                                    'interface_name': interface_name,
                                    'networks': interface_networks
                                })
                                
                        except ValueError as e:
                            print(f"Error parsing trunk VLANs '{trunk_vlans}' for interface {interface_name}: {e}")
        
        return trunk_interfaces
    
    def attach_access_vlan_to_switch_interface(self, fabric_name: str, serial_number: str, 
                                             interface_name: str, network_name: str, vlan_id: int) -> bool:
        """
        Attach an access VLAN to a specific switch interface.
        
        Args:
            fabric_name: Name of the fabric
            serial_number: Serial number of the switch
            interface_name: Name of the interface
            network_name: Name of the network
            vlan_id: VLAN ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"  Processing {interface_name} (ACCESS) -> Network: {network_name} (VLAN {vlan_id})")
            
            success = network_api.attach_network(
                fabric_name=fabric_name,
                network_name=network_name,
                serial_number=serial_number,
                switch_ports=interface_name,
                vlan=vlan_id
            )
            
            if success:
                print(f"    ✓ Successfully attached")
            else:
                print(f"    ✗ Failed to attach")
                
            return success
            
        except Exception as e:
            print(f"    ✗ Error attaching: {e}")
            return False
    
    def attach_trunk_vlans_to_switch_interface(self, fabric_name: str, serial_number: str, 
                                             interface_name: str, networks: List[Dict[str, Any]]) -> bool:
        """
        Attach trunk VLANs to a specific switch interface.
        
        Args:
            fabric_name: Name of the fabric
            serial_number: Serial number of the switch
            interface_name: Name of the interface
            networks: List of network configurations
            
        Returns:
            bool: True if all attachments successful, False otherwise
        """
        all_success = True
        
        network_names = ', '.join([f"{n['network_name']} (VLAN {n['vlan_id']})" for n in networks])
        print(f"  Processing {interface_name} (TRUNK) -> Networks: {network_names}")
        
        for network_info in networks:
            try:
                print(f"    Attaching network '{network_info['network_name']}' (VLAN {network_info['vlan_id']})")
                
                success = network_api.attach_network(
                    fabric_name=fabric_name,
                    network_name=network_info['network_name'],
                    serial_number=serial_number,
                    switch_ports=interface_name,
                    vlan=network_info['vlan_id']
                )
                
                if success:
                    print(f"      ✓ Successfully attached")
                else:
                    print(f"      ✗ Failed to attach")
                    all_success = False
                    
            except Exception as e:
                print(f"      ✗ Error attaching VLAN {network_info['vlan_id']}: {e}")
                all_success = False
        
        return all_success
    
    def detach_access_vlan_from_switch_interface(self, fabric_name: str, serial_number: str, 
                                               interface_name: str, network_name: str, vlan_id: int) -> bool:
        """
        Detach an access VLAN from a specific switch interface.
        
        Args:
            fabric_name: Name of the fabric
            serial_number: Serial number of the switch
            interface_name: Name of the interface
            network_name: Name of the network
            vlan_id: VLAN ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"  Processing {interface_name} (ACCESS) -> Network: {network_name} (VLAN {vlan_id})")
            
            success = network_api.detach_network(
                fabric_name=fabric_name,
                network_name=network_name,
                serial_number=serial_number,
                detach_switch_ports=interface_name,
                vlan=vlan_id
            )
            
            if success:
                print(f"    ✓ Successfully detached")
            else:
                print(f"    ✗ Failed to detach")
                
            return success
            
        except Exception as e:
            print(f"    ✗ Error detaching: {e}")
            return False
    
    def detach_trunk_vlans_from_switch_interface(self, fabric_name: str, serial_number: str, 
                                               interface_name: str, networks: List[Dict[str, Any]]) -> bool:
        """
        Detach trunk VLANs from a specific switch interface.
        
        Args:
            fabric_name: Name of the fabric
            serial_number: Serial number of the switch
            interface_name: Name of the interface
            networks: List of network configurations
            
        Returns:
            bool: True if all detachments successful, False otherwise
        """
        all_success = True
        
        network_names = ', '.join([f"{n['network_name']} (VLAN {n['vlan_id']})" for n in networks])
        print(f"  Processing {interface_name} (TRUNK) -> Networks: {network_names}")
        
        for network_info in networks:
            try:
                print(f"    Detaching network '{network_info['network_name']}' (VLAN {network_info['vlan_id']})")
                
                success = network_api.detach_network(
                    fabric_name=fabric_name,
                    network_name=network_info['network_name'],
                    serial_number=serial_number,
                    detach_switch_ports=interface_name,
                    vlan=network_info['vlan_id']
                )
                
                if success:
                    print(f"      ✓ Successfully detached")
                else:
                    print(f"      ✗ Failed to detach")
                    all_success = False
                    
            except Exception as e:
                print(f"      ✗ Error detaching VLAN {network_info['vlan_id']}: {e}")
                all_success = False
        
        return all_success
    
    def attach_networks_to_switch(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """
        Attach all networks to a switch based on its interface configuration.
        
        Args:
            fabric_name: Name of the fabric
            role: Role of the switch
            switch_name: Name of the switch
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Attaching networks to switch '{switch_name}' in fabric '{fabric_name}'...")
            
            # Load switch configuration
            switch_config = self.get_switch_configuration(fabric_name, role, switch_name)
            if not switch_config:
                return False
            
            # Get switch serial number
            serial_number = switch_config.get('Serial Number')
            if not serial_number:
                print(f"Serial number not found for switch {switch_name}")
                return False
            
            # Parse access interfaces
            access_interfaces = self.parse_access_interfaces(switch_config, fabric_name)
            
            # Parse trunk interfaces
            trunk_interfaces = self.parse_trunk_interfaces(switch_config, fabric_name)
            
            # Show summary of interfaces to be processed
            print(f"Found {len(access_interfaces)} access interface(s) and {len(trunk_interfaces)} trunk interface(s)")
            
            all_success = True
            
            # Attach access interfaces
            for access_interface in access_interfaces:
                success = self.attach_access_vlan_to_switch_interface(
                    fabric_name=fabric_name,
                    serial_number=serial_number,
                    interface_name=access_interface['interface_name'],
                    network_name=access_interface['network_name'],
                    vlan_id=access_interface['vlan_id']
                )
                if not success:
                    all_success = False
            
            # Attach trunk interfaces
            for trunk_interface in trunk_interfaces:
                success = self.attach_trunk_vlans_to_switch_interface(
                    fabric_name=fabric_name,
                    serial_number=serial_number,
                    interface_name=trunk_interface['interface_name'],
                    networks=trunk_interface['networks']
                )
                if not success:
                    all_success = False
            
            if all_success:
                self.message_formatter.success("attach", f"{switch_name} networks", "Network")
            else:
                self.message_formatter.failure("attach", f"{switch_name} networks", "Network")
            
            return all_success
            
        except Exception as e:
            self.message_formatter.error("attach", f"{switch_name} networks", e, "Network")
            return False
    
    def detach_networks_from_switch(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """
        Detach all networks from a switch based on its interface configuration.
        
        Args:
            fabric_name: Name of the fabric
            role: Role of the switch
            switch_name: Name of the switch
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Detaching networks from switch '{switch_name}' in fabric '{fabric_name}'...")
            
            # Load switch configuration
            switch_config = self.get_switch_configuration(fabric_name, role, switch_name)
            if not switch_config:
                return False
            
            # Get switch serial number
            serial_number = switch_config.get('Serial Number')
            if not serial_number:
                print(f"Serial number not found for switch {switch_name}")
                return False
            
            # Parse access interfaces
            access_interfaces = self.parse_access_interfaces(switch_config, fabric_name)
            
            # Parse trunk interfaces
            trunk_interfaces = self.parse_trunk_interfaces(switch_config, fabric_name)
            
            # Show summary of interfaces to be processed
            print(f"Found {len(access_interfaces)} access interface(s) and {len(trunk_interfaces)} trunk interface(s)")
            
            all_success = True
            
            # Detach access interfaces
            for access_interface in access_interfaces:
                success = self.detach_access_vlan_from_switch_interface(
                    fabric_name=fabric_name,
                    serial_number=serial_number,
                    interface_name=access_interface['interface_name'],
                    network_name=access_interface['network_name'],
                    vlan_id=access_interface['vlan_id']
                )
                if not success:
                    all_success = False
            
            # Detach trunk interfaces
            for trunk_interface in trunk_interfaces:
                success = self.detach_trunk_vlans_from_switch_interface(
                    fabric_name=fabric_name,
                    serial_number=serial_number,
                    interface_name=trunk_interface['interface_name'],
                    networks=trunk_interface['networks']
                )
                if not success:
                    all_success = False
            
            if all_success:
                self.message_formatter.success("detach", f"{switch_name} networks", "Network")
            else:
                self.message_formatter.failure("detach", f"{switch_name} networks", "Network")
            
            return all_success
            
        except Exception as e:
            self.message_formatter.error("detach", f"{switch_name} networks", e, "Network")
            return False
