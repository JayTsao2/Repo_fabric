#!/usr/bin/env python3
"""
Common Utilities - Shared functionality across fabric and VRF modules

This module provides common functionality used by both fabric and VRF modules:
- Standard imports and path setup
- Common message formatting
- Error handling utilities
- Standard operation patterns
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional, Callable
from enum import Enum

# Ensure API modules are accessible
_root_path = Path(__file__).parent.parent.absolute()
if str(_root_path) not in sys.path:
    sys.path.append(str(_root_path))

class OperationType(Enum):
    """Standard operation types for consistent messaging."""
    CREATE = "create"
    UPDATE = "update" 
    DELETE = "delete"
    ATTACH = "attach"
    DETACH = "detach"

class MessageFormatter:
    """Standardized message formatting for operations."""
    
    @staticmethod
    def success(operation_type: str, resource_name: str, resource_type: str = "") -> None:
        """Print standardized success message."""
        type_suffix = f" {resource_type}" if resource_type else ""
        print(f"✅ SUCCESS: {operation_type.title()}{type_suffix} - {resource_name}")
        
        # Operation-specific success messages
        if operation_type.lower() == "create":
            print(f"   {resource_type or 'Resource'} '{resource_name}' has been created successfully")
        elif operation_type.lower() == "update":
            print(f"   {resource_type or 'Resource'} '{resource_name}' has been updated successfully")
        elif operation_type.lower() == "delete":
            print(f"   {resource_type or 'Resource'} '{resource_name}' has been deleted successfully")
        elif operation_type.lower() in ["attach", "detach"]:
            action = "attached to" if operation_type.lower() == "attach" else "detached from"
            print(f"   {resource_type or 'Resource'} '{resource_name}' has been {action} switches successfully")
    
    @staticmethod
    def failure(operation_type: str, resource_name: str, resource_type: str = "") -> None:
        """Print standardized failure message."""
        type_suffix = f" {resource_type}" if resource_type else ""
        print(f"❌ FAILED: {operation_type.title()}{type_suffix} - {resource_name}")
        
        # Operation-specific failure messages
        operation_verb = operation_type.lower().rstrip('e') if operation_type.lower().endswith('e') else operation_type.lower()
        print(f"   Failed to {operation_verb} {resource_type.lower() or 'resource'} '{resource_name}'")
    
    @staticmethod
    def error(operation_type: str, resource_name: str, error: Exception, resource_type: str = "") -> None:
        """Print standardized error message with exception details."""
        print(f"❌ Error {operation_type.lower()}ing {resource_type or 'resource'} {resource_name}: {error}")
        MessageFormatter.failure(operation_type, resource_name, resource_type)

class OperationExecutor:
    """Standard operation execution pattern with consistent error handling and messaging."""
    
    @staticmethod
    def execute_operation(
        operation_name: str,
        resource_name: str, 
        operation_func: Callable[[], bool],
        resource_type: str = "",
        pre_operation_message: Optional[str] = None
    ) -> bool:
        """
        Execute an operation with standardized error handling and messaging.
        
        Args:
            operation_name: Name of the operation (create, update, delete, etc.)
            resource_name: Name of the resource being operated on
            operation_func: Function that performs the actual operation
            resource_type: Type of resource (Fabric, VRF, etc.)
            pre_operation_message: Optional message to display before operation
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if pre_operation_message:
                print(f"\n=== {pre_operation_message} ===")
            
            success = operation_func()
            
            if success:
                MessageFormatter.success(operation_name, resource_name, resource_type)
                return True
            else:
                MessageFormatter.failure(operation_name, resource_name, resource_type)
                return False
                
        except Exception as e:
            MessageFormatter.error(operation_name, resource_name, e, resource_type)
            return False

def setup_module_path(file_path: str) -> None:
    """
    Standard path setup for modules.
    
    Args:
        file_path: __file__ from the calling module
    """
    parent_path = str(Path(file_path).parent.parent.absolute())
    if parent_path not in sys.path:
        sys.path.append(parent_path)