#!/usr/bin/env python3
"""
Network Update Module

This module handles the updating of networks using YAML configuration.
"""

import sys
from pathlib import Path

# Setup module path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from modules.network import update_network as core_update_network
from modules.common_utils import MessageFormatter

class NetworkUpdater:
    """Handles network update operations."""
    
    def __init__(self):
        """Initialize the NetworkUpdater."""
        self.message_formatter = MessageFormatter()
    
    def update_network(self, fabric_name: str, network_name: str) -> bool:
        """
        Update a network using YAML configuration.
        
        Args:
            fabric_name: Name of the fabric
            network_name: Name of the network
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Updating network '{network_name}' in fabric '{fabric_name}'...")
            
            success = core_update_network(fabric_name, network_name)
            
            if success:
                self.message_formatter.success("update", network_name, "Network")
            else:
                self.message_formatter.failure("update", network_name, "Network")
                
            return success
            
        except Exception as e:
            self.message_formatter.error("update", network_name, e, "Network")
            return False
