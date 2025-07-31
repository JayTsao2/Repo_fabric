#!/usr/bin/env python3
"""
Network Management Module - Core Components

Provides YAML-based network management for Cisco NDFC:
- Network CRUD operations with configuration merging
- Template payload generation with field mapping
- Corp defaults integration and Layer 2 Only support
"""

# Import the NetworkManager and related components from network.py
from .network import NetworkManager, NetworkTemplateConfig, NetworkPayload

# --- Expose the NetworkManager class and dataclasses ---
__all__ = ['NetworkManager', 'NetworkTemplateConfig', 'NetworkPayload']
