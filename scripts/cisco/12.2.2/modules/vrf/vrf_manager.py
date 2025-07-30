#!/usr/bin/env python3
"""
VRF Manager - Unified VRF Management Interface

This module provides a clean, unified interface for all VRF operations.
It orchestrates VRF operations while delegating to specialized components.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.absolute()))

# Import VRF components with absolute imports to avoid circular imports
from modules.vrf.vrf_operations import VRFOperations
from modules.vrf.attach_vrf import VRFAttachment
import api.vrf as vrf_api


class VRFManager:
    """
    Unified VRF management interface.
    Orchestrates VRF operations while delegating to specialized components.
    """
    
    def __init__(self):
        """Initialize the VRF manager with required components."""
        self._operations = None
        self._attacher = None
    
    @property
    def operations(self) -> VRFOperations:
        """Lazy initialization of VRFOperations."""
        if self._operations is None:
            self._operations = VRFOperations()
        return self._operations
    
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
            print(f"Creating {vrf_name} in {fabric_name}")
            return self.operations.create_vrf(vrf_name)
            
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
            print(f"Updating {vrf_name} in {fabric_name}")
            return self.operations.update_vrf(vrf_name)
        except Exception as e:
            print(f"❌ Error updating VRF {vrf_name}: {e}")
            return False
    
    def delete_vrf(self, fabric_name: str, vrf_name: str) -> bool:
        """
        Delete a VRF from a fabric.
        
        Args:
            fabric_name: Name of the fabric
            vrf_name: Name of the VRF to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Deleting {vrf_name} from {fabric_name}")
            return vrf_api.delete_vrf(fabric_name, vrf_name)

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
            print(f"Attaching VRF to {switch_name} ({role}) in {fabric_name}")
            return  self.attacher.manage_vrf_by_switch(fabric_name, role, switch_name, operation="attach")
            
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
            print(f"Detaching VRF from {switch_name} ({role}) in {fabric_name}")
            return self.attacher.manage_vrf_by_switch(fabric_name, role, switch_name, operation="detach")
            
        except Exception as e:
            print(f"❌ Error detaching VRF from switch {switch_name}: {e}")
            return False