#!/usr/bin/env python3
"""
VRF Manager - Unified VRF Management Interface

This module provides a clean, unified interface for all VRF operations with:
- Consistent parameter ordering (fabric_name, vrf_name)
- Centralized error handling and validation
- Clear separation between VRF lifecycle and attachment operations
- Improved logging and user feedback
"""
# Import VRF components with absolute imports to avoid circular imports
from modules.vrf.vrf_operations import VRFOperations
from modules.vrf.attach_vrf import VRFAttachment
import api.vrf as vrf_api


class VRFManager:
    """
    Unified VRF Management Interface
    
    Provides a clean, consistent interface for all VRF operations:
    - VRF lifecycle management (create, update, delete)
    - VRF attachment management (attach, detach)
    - Centralized error handling and logging
    
    All methods follow consistent parameter ordering: fabric_name, vrf_name/switch_name
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
    def create_vrf(self, fabric_name: str, vrf_name: str) -> bool:
        """
        Create a VRF with validation and error handling.
        
        Args:
            fabric_name: Name of the fabric where VRF will be created
            vrf_name: Name of the VRF to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"[VRF] Creating VRF {vrf_name} in fabric {fabric_name}")
        return self.operations.create_vrf(fabric_name, vrf_name)
    
    def update_vrf(self, fabric_name: str, vrf_name: str) -> bool:
        """
        Update an existing VRF.
        
        Args:
            fabric_name: Name of the fabric containing the VRF
            vrf_name: Name of the VRF to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"[VRF] Updating VRF {vrf_name} in fabric {fabric_name}")
        return self.operations.update_vrf(fabric_name, vrf_name)
    
    def delete_vrf(self, fabric_name: str, vrf_name: str) -> bool:
        """
        Delete a VRF from a fabric.
        
        Args:
            fabric_name: Name of the fabric
            vrf_name: Name of the VRF to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"[VRF] Deleting VRF '{vrf_name}' from fabric '{fabric_name}'")
        return vrf_api.delete_vrf(fabric_name, vrf_name)
    
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
        print(f"[VRF] Attaching VRF to switch {switch_name} ({role}) in fabric {fabric_name}")
        return self.attacher.manage_vrf_by_switch(fabric_name, role, switch_name, operation="attach")
    
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
        print(f"[VRF] Detaching VRF from switch {switch_name} ({role}) in fabric {fabric_name}")
        return self.attacher.manage_vrf_by_switch(fabric_name, role, switch_name, operation="detach")