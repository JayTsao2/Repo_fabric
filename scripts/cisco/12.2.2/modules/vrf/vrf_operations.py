#!/usr/bin/env python3
"""
VRF Operations - Unified VRF Create and Update Operations

This module handles VRF lifecycle operations with:
- Centralized configuration validation
- Fabric consistency checking
- Enhanced error handling and logging
- Template payload generation and validation
"""

import sys
from pathlib import Path

import api.vrf as vrf_api
from modules.config_utils import validate_configuration_files
from . import VRFBuilder, VRFPayloadGenerator

class VRFOperations:
    """Handles unified VRF create and update operations."""
    
    def __init__(self):
        self.builder = VRFBuilder()
        self.payload_generator = VRFPayloadGenerator()
    
    def _execute_vrf_operation(self, fabric_name: str, vrf_name: str, operation: str) -> bool:
        """
        Execute VRF operation (create or update).
        
        Args:
            fabric_name: Name of the fabric
            vrf_name: Name of the VRF from the configuration
            operation: Either "create" or "update"
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"{operation.title()}ing VRF '{vrf_name}' in fabric '{fabric_name}'")
            
            # Get configuration
            config = self.builder.get_vrf_config()
            print(f"Using config file: {config.config_path}")
            
            # Validate required files exist
            required_files = [
                config.config_path, config.defaults_path, 
                config.field_mapping_path
            ]
            files_exist, missing_files = validate_configuration_files(required_files)
            if not files_exist:
                print("Missing required configuration files:")
                for file in missing_files:
                    print(f"   - {file}")
                return False
            
            # Generate payloads
            main_payload, template_payload = self.payload_generator.prepare_vrf_payload(config, fabric_name, vrf_name)
            if not main_payload or not template_payload:
                print(f"Failed to generate payload for VRF {operation}")
                return False            # Choose the appropriate API function based on operation
            if operation == "create":
                success = vrf_api.create_vrf(
                    fabric_name=fabric_name,
                    vrf_payload=main_payload,
                    template_payload=template_payload
                )
            else:  # update
                success = vrf_api.update_vrf(
                    vrf_name=vrf_name,
                    fabric_name=fabric_name,
                    vrf_payload=main_payload,
                    template_payload=template_payload
                )
            
            return success
                
        except Exception as e:
            print(f"Error {operation}ing VRF '{vrf_name}' in fabric '{fabric_name}': {e}")
            return False

    def create_vrf(self, fabric_name: str, vrf_name: str) -> bool:
        """Create a VRF in the specified fabric."""
        return self._execute_vrf_operation(fabric_name, vrf_name, "create")

    def update_vrf(self, fabric_name: str, vrf_name: str) -> bool:
        """Update a VRF in the specified fabric."""
        return self._execute_vrf_operation(fabric_name, vrf_name, "update")
