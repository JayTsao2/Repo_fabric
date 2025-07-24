#!/usr/bin/env python3
"""
VRF Builder - Create Operations

This module handles VRF creation operations:
- Creating VRFs with template configurations
- Managing VRF attachments
"""

from typing import Dict, Any, List, Optional
from modules.common_utils import setup_module_path, OperationExecutor, MessageFormatter
setup_module_path(__file__)

import api.vrf as vrf_api
from modules.config_utils import validate_configuration_files, load_yaml_file
from . import (
    VRFTemplate, 
    BaseVRFMethods, 
)

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
            print(f"\n=== Creating VRF: {vrf_name} ===")
            
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
            return OperationExecutor.execute_operation(
                operation_name="create",
                resource_name=vrf_name,
                resource_type="VRF",
                pre_operation_message=f"Creating VRF: {vrf_name}",
                operation_func=lambda: vrf_api.create_vrf(
                    fabric_name=fabric_name,
                    vrf_payload=main_payload,
                    template_payload=template_payload
                )
            )
                
        except Exception as e:
            MessageFormatter.error("create", vrf_name, e, "VRF")
            return False

def main():
    """
    Main function for VRF creation operations.
    """
    vrf_creator = VRFCreator()
    
    print("🏗️  VRF Creator - Network VRF Creation Tool")
    print("=" * 60)
    
    # Configuration - Update these values as needed
    vrf_to_create = "bluevrf"
    
    # --- Create VRF ---
    
    # Create VRF (fabric name is extracted from VRF configuration)
    success = vrf_creator.create_vrf(vrf_to_create)
    if not success:
        print(f"Failed to create VRF: {vrf_to_create}")
        return 1
    
    print("\n🎉 VRF creation process completed successfully!")
    return 0

if __name__ == "__main__":
    from modules.common_utils import create_main_function_wrapper
    main_wrapper = create_main_function_wrapper("VRF Creator", main)
    main_wrapper()
