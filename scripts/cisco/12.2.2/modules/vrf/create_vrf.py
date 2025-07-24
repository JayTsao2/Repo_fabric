#!/usr/bin/env python3
"""
VRF Builder - Create Operations

This module handles VRF creation operations:
- Creating VRFs with template configurations
- Managing VRF attachments
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path to access api and modules
sys.path.append(str(Path(__file__).parent.parent.absolute()))
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
            
            # Call VRF API for creation
            success = vrf_api.create_vrf(
                fabric_name=fabric_name,
                vrf_payload=main_payload,
                template_payload=template_payload
            )
            
            if success:
                print(f"✅ SUCCESS: VRF - {vrf_name}")
                print(f"   VRF '{vrf_name}' has been created successfully")
                return True
            else:
                print(f"❌ FAILED: VRF - {vrf_name}")
                print(f"   Failed to create VRF '{vrf_name}'")
                return False
                
        except Exception as e:
            print(f"❌ Error creating VRF {vrf_name}: {e}")
            print(f"❌ FAILED: VRF - {vrf_name}")
            print(f"   Failed to create VRF '{vrf_name}'")
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
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
