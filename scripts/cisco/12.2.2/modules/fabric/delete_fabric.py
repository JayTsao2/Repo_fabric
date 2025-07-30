#!/usr/bin/env python3
"""
Fabric Builder - Delete Operations

This module handles fabric deletion operations:
- Deleting VXLAN EVPN Fabrics
- Deleting Multi-Site Domains (MSD)
- Deleting Inter-Site Networks (ISN)
"""

from modules.common_utils import setup_module_path, OperationExecutor
setup_module_path(__file__)

import api.fabric as fabric_api

class FabricDeleter:
    """Handles fabric deletion operations."""
    
    def delete_fabric(self, fabric_name: str) -> bool:
        """
        Delete any fabric by name.
        
        Args:
            fabric_name: Name of the fabric to delete
        
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"\n=== Deleting Fabric: {fabric_name} ===")
        
        try:
            # Execute the fabric deletion operation
            return OperationExecutor.execute_operation(
                operation_name="delete",
                resource_name=fabric_name,
                resource_type="Fabric",
                pre_operation_message=f"Deleting Fabric: {fabric_name}",
                operation_func=lambda: fabric_api.delete_fabric(fabric_name=fabric_name)
            )
                
        except Exception as e:
            print(f"❌ Error deleting fabric {fabric_name}: {e}")
            return False


def main():
    """
    Main function for fabric deletion operations.
    """
    fabric_deleter = FabricDeleter()
    
    print("🗑️  Fabric Deleter - Network Fabric Deletion Tool")
    print("=" * 60)
    
    # Configuration - Update these values as needed
    fabric_site_to_delete = "Site3-Test"
    msd_to_delete = "MSD-Test_15"
    isn_to_delete = "ISN-Test"
    
    # --- Delete Existing Fabrics ---
    
    # Delete VXLAN EVPN fabric (fabric type determined from YAML if available)
    success = fabric_deleter.delete_fabric(fabric_site_to_delete)
    if not success:
        print(f"Failed to delete fabric: {fabric_site_to_delete}")
        return 1
    
    # Delete Multi-Site Domain (fabric type determined from YAML if available)
    success = fabric_deleter.delete_fabric(msd_to_delete)
    if not success:
        print(f"Failed to delete fabric: {msd_to_delete}")
        return 1
    
    # Delete Inter-Site Network (fabric type determined from YAML if available)
    success = fabric_deleter.delete_fabric(isn_to_delete)
    if not success:
        print(f"Failed to delete fabric: {isn_to_delete}")
        return 1
    
    print("\n🎉 Fabric deletion process completed successfully!")
    return 0


if __name__ == "__main__":
    from modules.common_utils import create_main_function_wrapper
    main_wrapper = create_main_function_wrapper("Fabric Deleter", main)
    main_wrapper()
