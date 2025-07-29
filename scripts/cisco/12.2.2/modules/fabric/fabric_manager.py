#!/usr/bin/env python3
"""
Fabric Manager - Unified Fabric Management Interface

This module provides a clean, unified interface for all fabric operations.
It orchestrates fabric operations while delegating to specialized components.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from .create_fabric import FabricCreator
from .update_fabric import FabricUpdater
from .delete_fabric import FabricDeleter
import api.fabric as fabric_api


class FabricManager:
    """
    Unified fabric management interface.
    Orchestrates fabric operations while delegating to specialized components.
    """
    
    def __init__(self):
        """Initialize the fabric manager with required components."""
        self._creator = None
        self._updater = None
        self._deleter = None
    
    @property
    def creator(self) -> FabricCreator:
        """Lazy initialization of FabricCreator."""
        if self._creator is None:
            self._creator = FabricCreator()
        return self._creator
    
    @property
    def updater(self) -> FabricUpdater:
        """Lazy initialization of FabricUpdater."""
        if self._updater is None:
            self._updater = FabricUpdater()
        return self._updater
    
    @property
    def deleter(self) -> FabricDeleter:
        """Lazy initialization of FabricDeleter."""
        if self._deleter is None:
            self._deleter = FabricDeleter()
        return self._deleter
    
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
            success = self.creator.build_fabric(fabric_name)
            if success:
                print(f"✅ Successfully created fabric {fabric_name}")
            else:
                print(f"❌ Failed to create fabric {fabric_name}")
            return success
            
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
            success = self.updater.update_fabric(fabric_name)
            if success:
                print(f"✅ Successfully updated fabric {fabric_name}")
            else:
                print(f"❌ Failed to update fabric {fabric_name}")
            return success
            
        except Exception as e:
            print(f"❌ Error updating fabric {fabric_name}: {e}")
            return False
    
    def delete_fabric(self, fabric_name: str, force: bool = False) -> bool:
        """
        Delete a fabric with optional confirmation.
        
        Args:
            fabric_name: Name of the fabric to delete
            force: Skip confirmation prompt if True
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not force:
                confirm = input(f"Are you sure you want to delete fabric '{fabric_name}'? (y/N): ")
                if confirm.lower() not in ['y', 'yes']:
                    print("❌ Delete operation cancelled by user")
                    return True  # Not an error, user chose to cancel
            
            print(f"Deleting fabric: {fabric_name}")
            success = self.deleter.delete_fabric(fabric_name)
            if success:
                print(f"✅ Successfully deleted fabric {fabric_name}")
            else:
                print(f"❌ Failed to delete fabric {fabric_name}")
            return success
            
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
            success = fabric_api.recalculate_config(fabric_name)
            if success:
                print(f"✅ Successfully recalculated configuration for fabric {fabric_name}")
            else:
                print(f"❌ Failed to recalculate configuration for fabric {fabric_name}")
            return success
            
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
            result = fabric_api.get_pending_config(fabric_name)
            if result is not None:
                print(f"✅ Successfully retrieved pending configuration for fabric {fabric_name}")
            else:
                print(f"❌ Failed to retrieve pending configuration for fabric {fabric_name}")
            return result
            
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
            success = fabric_api.deploy_fabric_config(fabric_name)
            if success:
                print(f"✅ Successfully deployed configuration for fabric {fabric_name}")
            else:
                print(f"❌ Failed to deploy configuration for fabric {fabric_name}")
            return success
            
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
            success = self.creator.link_fabrics(parent_fabric, child_fabric)
            if success:
                print(f"✅ Successfully added '{child_fabric}' to MSD '{parent_fabric}'")
            else:
                print(f"❌ Failed to add '{child_fabric}' to MSD '{parent_fabric}'")
            return success
            
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
            if not force:
                confirm = input(f"Are you sure you want to remove '{child_fabric}' from MSD '{parent_fabric}'? (y/N): ")
                if confirm.lower() not in ['y', 'yes']:
                    print("❌ Remove operation cancelled by user")
                    return True  # Not an error, user chose to cancel
            
            print(f"Removing fabric '{child_fabric}' from MSD '{parent_fabric}'")
            success = self.creator.unlink_fabrics(parent_fabric, child_fabric)
            if success:
                print(f"✅ Successfully removed '{child_fabric}' from MSD '{parent_fabric}'")
            else:
                print(f"❌ Failed to remove '{child_fabric}' from MSD '{parent_fabric}'")
            return success
            
        except Exception as e:
            print(f"❌ Error removing fabric from MSD: {e}")
            return False
    
    # Workflow Operations
    def full_deployment_workflow(self, fabric_name: str) -> bool:
        """
        Execute a complete deployment workflow: recalculate -> get-pending -> deploy.
        
        Args:
            fabric_name: Name of the fabric to deploy
            
        Returns:
            bool: True if all steps successful, False otherwise
        """
        print(f"Starting full deployment workflow for fabric: {fabric_name}")
        
        # Step 1: Recalculate configuration
        if not self.recalculate_config(fabric_name):
            print("❌ Deployment workflow failed at recalculation step")
            return False
        
        # Step 2: Get pending configuration for review
        if not self.get_pending_config(fabric_name):
            print("❌ Deployment workflow failed at pending config step")
            return False
        
        # Step 3: Ask for confirmation before deployment
        confirm = input("Review the pending.txt file. Continue with deployment? (y/N): ")
        if confirm.lower() not in ['y', 'yes']:
            print("❌ Deployment cancelled by user")
            return False
        
        # Step 4: Deploy configuration
        if not self.deploy_fabric(fabric_name):
            print("❌ Deployment workflow failed at deployment step")
            return False
        
        print(f"✅ Full deployment workflow completed successfully for fabric {fabric_name}")
        return True
