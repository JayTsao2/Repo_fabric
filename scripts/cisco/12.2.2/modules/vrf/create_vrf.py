#!/usr/bin/env python3
"""
VRF Builder - Create Operations

This module handles VRF creation operations:
- Creating VRFs with template configurations
- Managing VRF attachments
"""

from modules.common_utils import setup_module_path, OperationExecutor
setup_module_path(__file__)

import api.vrf as vrf_api
from modules.config_utils import validate_configuration_files
from . import BaseVRFMethods

class VRFCreator(BaseVRFMethods):
    """Handles VRF creation operations."""
    
    def create_vrf(self, vrf_name: str) -> bool:
        """
        Create a VRF using fabric information from the VRF configuration.
        
        Args:
            vrf_name: Name of the VRF from the configuration
            
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
                print(f"Failed to generate payload for VRF creation")
                return False
            
            # Execute the VRF creation operation
            return vrf_api.create_vrf(
                fabric_name=fabric_name,
                vrf_payload=main_payload,
                template_payload=template_payload
            )
                
        except Exception as e:
            print(f"❌ Error creating VRF {vrf_name}: {e}")
            return False
