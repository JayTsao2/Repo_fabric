#!/usr/bin/env python3
"""
VRF Builder - Delete Operations

This module handles VRF deletion operations:
- Deleting VRFs from fabrics
- Managing VRF detachment from switches
"""

from modules.common_utils import setup_module_path, OperationExecutor, MessageFormatter
setup_module_path(__file__)

import api.vrf as vrf_api
from modules.config_utils import load_yaml_file
from . import BaseVRFMethods

class VRFDeleter(BaseVRFMethods):
    """Handles VRF deletion operations."""
    
    def delete_vrf(self, vrf_name: str) -> bool:
        """
        Delete a VRF using fabric information from VRF configuration.
        
        Args:
            vrf_name: Name of the VRF to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get fabric name from VRF configuration
            config = self.builder.get_vrf_config()
            _, _, fabric_name = self.payload_generator.prepare_vrf_payload(config, vrf_name)
            
            if not fabric_name:
                print(f"Could not determine fabric for VRF {vrf_name}")
                return False
            
            print(f"\n=== Deleting VRF: {vrf_name} from Fabric: {fabric_name} ===")
            
            # Execute the VRF deletion operation
            return OperationExecutor.execute_operation(
                operation_name="delete",
                resource_name=vrf_name,
                resource_type="VRF",
                operation_func=lambda: vrf_api.delete_vrf(fabric_name, vrf_name)
            )
                
        except Exception as e:
            MessageFormatter.error("delete", vrf_name, e, "VRF")
            return False

def main():
    """
    Main function for VRF deletion operations.
    """
    vrf_deleter = VRFDeleter()
    
    print("🗑️  VRF Deleter - Network VRF Deletion Tool")
    print("=" * 60)
    
    # Configuration - Update these values as needed
    vrf_to_delete = "bluevrf"
    
    # --- Delete VRF ---
    
    # Delete VRF (fabric name is extracted from VRF configuration, with confirmation)
    success = vrf_deleter.delete_vrf(vrf_to_delete)
    if not success:
        print(f"Failed to delete VRF: {vrf_to_delete}")
        return 1
    
    print("\n🎉 VRF deletion process completed successfully!")
    return 0

if __name__ == "__main__":
    from modules.common_utils import create_main_function_wrapper
    main_wrapper = create_main_function_wrapper("VRF Deleter", main)
    main_wrapper()
