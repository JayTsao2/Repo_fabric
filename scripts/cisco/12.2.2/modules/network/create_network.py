#!/usr/bin/env python3
"""
Network Creation Module

This module handles the creation of networks using YAML configuration.
"""

import sys
from pathlib import Path

# Setup module path
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from modules.network import create_network as core_create_network
from modules.common_utils import MessageFormatter

class NetworkCreator:
    """Handles network creation operations."""
    
    def __init__(self):
        """Initialize the NetworkCreator."""
        self.message_formatter = MessageFormatter()
    
    def create_network(self, fabric_name: str, network_name: str) -> bool:
        """
        Create a network using YAML configuration.
        
        Args:
            fabric_name: Name of the fabric
            network_name: Name of the network
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Creating network '{network_name}' in fabric '{fabric_name}'...")
            
            success = core_create_network(fabric_name, network_name)
            
            if success:
                self.message_formatter.success("create", network_name, "Network")
            else:
                self.message_formatter.failure("create", network_name, "Network")
                
            return success
            
        except Exception as e:
            self.message_formatter.error("create", network_name, e, "Network")
            return False
