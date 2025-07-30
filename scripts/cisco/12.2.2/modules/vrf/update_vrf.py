#!/usr/bin/env python3
"""
VRF Builder - Update Operations

This module handles VRF update operations:
- Updating VRFs with template configurations
- Managing VRF attachment updates
"""
from modules.common_utils import setup_module_path
setup_module_path(__file__)

import api.vrf as vrf_api
from modules.config_utils import validate_configuration_files
from . import BaseVRFMethods

class VRFUpdater(BaseVRFMethods):
    """Handles VRF update operations."""
    
    def update_vrf(self, vrf_name: str) -> bool:
        """
        Update a VRF using fabric information from the VRF configuration.
        
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
                print(f"Failed to generate payload for VRF update")
                return False
            
            # Execute the VRF update operation
            return vrf_api.update_vrf(
                vrf_name=vrf_name,
                fabric_name=fabric_name,
                vrf_payload=main_payload,
                template_payload=template_payload
            )
                
        except Exception as e:
            print(f"❌ Error updating VRF {vrf_name}: {e}")
            return False