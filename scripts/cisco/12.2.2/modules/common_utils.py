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

def setup_module_path(file_path: str) -> None:
    """
    Standard path setup for modules.
    
    Args:
        file_path: __file__ from the calling module
    """
    parent_path = str(Path(file_path).parent.parent.absolute())
    if parent_path not in sys.path:
        sys.path.append(parent_path)