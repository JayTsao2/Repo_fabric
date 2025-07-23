#!/usr/bin/env python3
"""
Fabric Builder - Delete Operations

This module handles fabric deletion operations:
- Deleting VXLAN EVPN Fabrics
- Deleting Multi-Site Domains (MSD)
- Deleting Inter-Site Networks (ISN)
"""

import sys
from pathlib import Path

# Add parent directory to path to access api and config_utils
sys.path.append(str(Path(__file__).parent.parent.absolute()))
import api.fabric as fabric_api
from config_utils import print_build_summary

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
            print(f"Calling delete_fabric API for {fabric_name}...")
            
            # Call fabric API for deletion
            success = fabric_api.delete_fabric(fabric_name=fabric_name)
            
            if success:
                print_build_summary("Fabric Deletion", fabric_name, True, "deleted")
                return True
            else:
                print_build_summary("Fabric Deletion", fabric_name, False, "deleted")
                return False
                
        except Exception as e:
            print(f"❌ Error deleting fabric {fabric_name}: {e}")
            print_build_summary("Fabric Deletion", fabric_name, False, "deleted")
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
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
