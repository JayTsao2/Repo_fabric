#!/usr/bin/env python3
"""
Network Deletion Module

This module handles the deletion of networks.
"""

import sys
from pathlib import Path

# Setup module path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from modules.network import delete_network as core_delete_network
from modules.common_utils import MessageFormatter

class NetworkDeleter:
    """Handles network deletion operations."""
    
    def __init__(self):
        """Initialize the NetworkDeleter."""
        self.message_formatter = MessageFormatter()
    
    def delete_network(self, fabric_name: str, network_name: str) -> bool:
        """
        Delete a network.
        
        Args:
            fabric_name: Name of the fabric
            network_name: Name of the network
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Deleting network '{network_name}' from fabric '{fabric_name}'...")
            
            success = core_delete_network(fabric_name, network_name)
            
            if success:
                self.message_formatter.success("delete", network_name, "Network")
            else:
                self.message_formatter.failure("delete", network_name, "Network")
                
            return success
            
        except Exception as e:
            self.message_formatter.error("delete", network_name, e, "Network")
            return False
