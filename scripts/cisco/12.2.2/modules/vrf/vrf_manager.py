#!/usr/bin/env python3
"""
VRF Manager - Unified VRF Management Interface

This module provides a clean, unified interface for all VRF operations.
It orchestrates VRF operations while delegating to specialized components.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.absolute()))

# Import VRF components with absolute imports to avoid circular imports
from modules.vrf.create_vrf import VRFCreator
from modules.vrf.update_vrf import VRFUpdater
from modules.vrf.delete_vrf import VRFDeleter
from modules.vrf.attach_vrf import VRFAttachment
import api.vrf as vrf_api


class VRFManager:
    """
    Unified VRF management interface.
    Orchestrates VRF operations while delegating to specialized components.
    """
    
    def __init__(self):
        """Initialize the VRF manager with required components."""
        self._creator = None
        self._updater = None
        self._deleter = None
        self._attacher = None
    
    @property
    def creator(self) -> VRFCreator:
        """Lazy initialization of VRFCreator."""
        if self._creator is None:
            self._creator = VRFCreator()
        return self._creator
    
    @property
    def updater(self) -> VRFUpdater:
        """Lazy initialization of VRFUpdater."""
        if self._updater is None:
            self._updater = VRFUpdater()
        return self._updater
    
    @property
    def deleter(self) -> VRFDeleter:
        """Lazy initialization of VRFDeleter."""
        if self._deleter is None:
            self._deleter = VRFDeleter()
        return self._deleter
    
    @property
    def attacher(self) -> VRFAttachment:
        """Lazy initialization of VRFAttachment."""
        if self._attacher is None:
            self._attacher = VRFAttachment()
        return self._attacher
    
    # Core VRF Operations
    def create_vrf(self, vrf_name: str, fabric_name: str) -> bool:
        """
        Create a VRF with validation and error handling.
        
        Args:
            vrf_name: Name of the VRF to create
            fabric_name: Name of the fabric where VRF will be created
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Creating VRF: {vrf_name} in fabric: {fabric_name}")
            success = self.creator.create_vrf(vrf_name)
            if success:
                print(f"✅ Successfully created VRF {vrf_name}")
            else:
                print(f"❌ Failed to create VRF {vrf_name}")
            return success
            
        except Exception as e:
            print(f"❌ Error creating VRF {vrf_name}: {e}")
            return False
    
    def update_vrf(self, vrf_name: str, fabric_name: str) -> bool:
        """
        Update an existing VRF.
        
        Args:
            vrf_name: Name of the VRF to update
            fabric_name: Name of the fabric containing the VRF
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Updating VRF: {vrf_name} in fabric: {fabric_name}")
            success = self.updater.update_vrf(vrf_name)
            if success:
                print(f"✅ Successfully updated VRF {vrf_name}")
            else:
                print(f"❌ Failed to update VRF {vrf_name}")
            return success
            
        except Exception as e:
            print(f"❌ Error updating VRF {vrf_name}: {e}")
            return False
    
    def delete_vrf(self, vrf_name: str) -> bool:
        """
        Delete a VRF.
        
        Args:
            vrf_name: Name of the VRF to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Deleting VRF: {vrf_name}")
            success = self.deleter.delete_vrf(vrf_name)
            if success:
                print(f"✅ Successfully deleted VRF {vrf_name}")
            else:
                print(f"❌ Failed to delete VRF {vrf_name}")
            return success
            
        except Exception as e:
            print(f"❌ Error deleting VRF {vrf_name}: {e}")
            return False
    
    # VRF Attachment Operations
    def attach_vrf(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """
        Attach VRF to switches based on interface configuration.
        
        Args:
            fabric_name: Name of the fabric
            role: Role of the switch (leaf, spine, etc.)
            switch_name: Name of the switch
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Attaching VRF to switch: {switch_name} (role: {role}) in fabric: {fabric_name}")
            success = self.attacher.manage_vrf_by_switch(fabric_name, role, switch_name, operation="attach")
            if success:
                print(f"✅ Successfully attached VRF to switch {switch_name}")
            else:
                print(f"❌ Failed to attach VRF to switch {switch_name}")
            return success
            
        except Exception as e:
            print(f"❌ Error attaching VRF to switch {switch_name}: {e}")
            return False
    
    def detach_vrf(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """
        Detach VRF from switches based on interface configuration.
        
        Args:
            fabric_name: Name of the fabric
            role: Role of the switch (leaf, spine, etc.)
            switch_name: Name of the switch
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Detaching VRF from switch: {switch_name} (role: {role}) in fabric: {fabric_name}")
            success = self.attacher.manage_vrf_by_switch(fabric_name, role, switch_name, operation="detach")
            if success:
                print(f"✅ Successfully detached VRF from switch {switch_name}")
            else:
                print(f"❌ Failed to detach VRF from switch {switch_name}")
            return success
            
        except Exception as e:
            print(f"❌ Error detaching VRF from switch {switch_name}: {e}")
            return False
    
    # Batch Operations
    def create_multiple_vrfs(self, vrf_names: List[str], fabric_name: str) -> Dict[str, bool]:
        """
        Create multiple VRFs in batch.
        
        Args:
            vrf_names: List of VRF names to create
            fabric_name: Name of the fabric
            
        Returns:
            Dict[str, bool]: Dictionary mapping VRF names to success status
        """
        results = {}
        print(f"Creating {len(vrf_names)} VRFs in fabric: {fabric_name}")
        
        for vrf_name in vrf_names:
            results[vrf_name] = self.create_vrf(vrf_name, fabric_name)
        
        successful = sum(1 for success in results.values() if success)
        print(f"\n📊 Batch VRF Creation Summary:")
        print(f"   ✅ Successful: {successful}/{len(vrf_names)}")
        print(f"   ❌ Failed: {len(vrf_names) - successful}/{len(vrf_names)}")
        
        return results
    
    # Utility Methods
    def get_vrf_status(self, vrf_name: str, fabric_name: str) -> Optional[Dict[str, Any]]:
        """
        Get VRF status information.
        
        Args:
            vrf_name: Name of the VRF
            fabric_name: Name of the fabric
            
        Returns:
            Optional[Dict[str, Any]]: VRF status information or None if failed
        """
        try:
            print(f"Getting status for VRF: {vrf_name} in fabric: {fabric_name}")
            # This would be implemented when the API supports it
            # For now, return basic info
            return {
                "vrf_name": vrf_name,
                "fabric_name": fabric_name,
                "status": "unknown"  # Would be populated by actual API call
            }
            
        except Exception as e:
            print(f"❌ Error getting VRF status: {e}")
            return None
    
    def list_vrfs(self, fabric_name: str) -> Optional[List[str]]:
        """
        List all VRFs in a fabric.
        
        Args:
            fabric_name: Name of the fabric
            
        Returns:
            Optional[List[str]]: List of VRF names or None if failed
        """
        try:
            print(f"Listing VRFs in fabric: {fabric_name}")
            # This would be implemented when the API supports it
            # For now, return empty list
            return []
            
        except Exception as e:
            print(f"❌ Error listing VRFs: {e}")
            return None
