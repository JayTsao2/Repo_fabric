#!/usr/bin/env python3
"""
VRF Builder - Unified Operations

This module handles both VRF creation and update operations:
- Creating/Updating VRFs with template configurations
- Managing VRF attachments
"""

from modules.common_utils import setup_module_path
setup_module_path(__file__)

import api.vrf as vrf_api
from modules.config_utils import validate_configuration_files
from . import BaseVRFMethods

class VRFOperations(BaseVRFMethods):
    """Handles unified VRF create and update operations."""
    
    def _execute_vrf_operation(self, vrf_name: str, operation: str) -> bool:
        """
        Execute VRF operation (create or update).
        
        Args:
            vrf_name: Name of the VRF from the configuration
            operation: Either "create" or "update"
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get configuration
            config = self.builder.get_vrf_config()
            
            # Validate required files exist
            required_files = [
                config.config_path, config.defaults_path, 
                config.field_mapping_path
            ]
            files_exist, missing_files = validate_configuration_files(required_files)
            if not files_exist:
                print("❌ Missing required configuration files:")
                for file in missing_files:
                    print(f"   - {file}")
                return False
            
            # Generate payloads
            main_payload, template_payload, fabric_name = self.payload_generator.prepare_vrf_payload(config, vrf_name)
            if not main_payload or not template_payload or not fabric_name:
                print(f"Failed to generate payload for VRF {operation}")
                return False
            
            # Choose the appropriate API function based on operation
            if operation == "create":
                api_func = lambda: vrf_api.create_vrf(
                    fabric_name=fabric_name,
                    vrf_payload=main_payload,
                    template_payload=template_payload
                )
            else:  # update
                api_func = lambda: vrf_api.update_vrf(
                    vrf_name=vrf_name,
                    fabric_name=fabric_name,
                    vrf_payload=main_payload,
                    template_payload=template_payload
                )
            
            # Execute the VRF operation
            return api_func()
                
        except Exception as e:
            print(f"❌ Error {operation} VRF {vrf_name}: {e}")
            return False

    def create_vrf(self, vrf_name: str) -> bool:
        return self._execute_vrf_operation(vrf_name, "create")

    def update_vrf(self, vrf_name: str) -> bool:
        return self._execute_vrf_operation(vrf_name, "update")
