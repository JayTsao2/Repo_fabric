#!/usr/bin/env python3
"""
Fabric Manager - Unified Fabric Management Interface

This module provides a clean, unified interface for all fabric operations.
It orchestrates fabric operations while delegating to specialized components.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

from .fabric_operations import FabricOperations
import api.fabric as fabric_api


class FabricManager:
    """
    Unified fabric management interface.
    Orchestrates fabric operations while delegating to specialized components.
    """
    
    def __init__(self):
        """Initialize the fabric manager with required components."""
        self._operations = None
    
    @property
    def operations(self) -> FabricOperations:
        """Lazy initialization of FabricOperations."""
        if self._operations is None:
            self._operations = FabricOperations()
        return self._operations
    
    # Core Fabric Operations
    def create_fabric(self, fabric_name: str) -> bool:
        """
        Create a fabric with validation and error handling.
        
        Args:
            fabric_name: Name of the fabric to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Creating fabric: {fabric_name}")
            return self.operations.create_fabric(fabric_name)
            
        except Exception as e:
            print(f"❌ Error creating fabric {fabric_name}: {e}")
            return False
    
    def update_fabric(self, fabric_name: str) -> bool:
        """
        Update an existing fabric.
        
        Args:
            fabric_name: Name of the fabric to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Updating fabric: {fabric_name}")
            return self.operations.update_fabric(fabric_name)
            
        except Exception as e:
            print(f"❌ Error updating fabric {fabric_name}: {e}")
            return False
    
    def delete_fabric(self, fabric_name: str) -> bool:
        """
        Delete a fabric.
        
        Args:
            fabric_name: Name of the fabric to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Deleting fabric: {fabric_name}")
            return fabric_api.delete_fabric(fabric_name)
        except Exception as e:
            print(f"❌ Error deleting fabric {fabric_name}: {e}")
            return False
    
    # Configuration Operations
    def recalculate_config(self, fabric_name: str) -> bool:
        """
        Recalculate fabric configuration.
        
        Args:
            fabric_name: Name of the fabric to recalculate
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Recalculating configuration for fabric: {fabric_name}")
            return fabric_api.recalculate_config(fabric_name)
            
        except Exception as e:
            print(f"❌ Error recalculating fabric {fabric_name}: {e}")
            return False
    
    def get_pending_config(self, fabric_name: str) -> Optional[Dict[str, Any]]:
        """
        Get pending configuration with formatted output.
        
        Args:
            fabric_name: Name of the fabric to get pending config for
            
        Returns:
            Optional[Dict[str, Any]]: Pending configuration data or None if failed
        """
        try:
            print(f"Getting pending configuration for fabric: {fabric_name}")
            fabric_api.get_pending_config(fabric_name)
            return
            
        except Exception as e:
            print(f"❌ Error getting pending config for fabric {fabric_name}: {e}")
            return None
    
    def deploy_fabric(self, fabric_name: str) -> bool:
        """
        Deploy fabric configuration.
        
        Args:
            fabric_name: Name of the fabric to deploy
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Deploying configuration for fabric: {fabric_name}")
            return fabric_api.deploy_fabric_config(fabric_name)
            
        except Exception as e:
            print(f"❌ Error deploying fabric {fabric_name}: {e}")
            return False
    
    # Multi-Site Domain Operations
    def add_to_msd(self, parent_fabric: str, child_fabric: str) -> bool:
        """
        Add a child fabric to a Multi-Site Domain.
        
        Args:
            parent_fabric: Name of the parent MSD fabric
            child_fabric: Name of the child fabric to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Adding fabric '{child_fabric}' to MSD '{parent_fabric}'")
            return fabric_api.add_MSD(parent_fabric, child_fabric)
            
        except Exception as e:
            print(f"❌ Error adding fabric to MSD: {e}")
            return False
    
    def remove_from_msd(self, parent_fabric: str, child_fabric: str, force: bool = False) -> bool:
        """
        Remove a child fabric from a Multi-Site Domain.
        
        Args:
            parent_fabric: Name of the parent MSD fabric
            child_fabric: Name of the child fabric to remove
            force: Skip confirmation prompt if True
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Removing fabric '{child_fabric}' from MSD '{parent_fabric}'")
            return fabric_api.remove_MSD(parent_fabric, child_fabric)
            
        except Exception as e:
            print(f"❌ Error removing fabric from MSD: {e}")
            return False