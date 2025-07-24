#!/usr/bin/env python3
"""
VRF Builder - Delete Operations

This module handles VRF deletion operations:
- Deleting VRFs from fabrics
- Managing VRF detachment from switches
"""

import sys
from pathlib import Path

# Add parent directory to path to access api and modules
sys.path.append(str(Path(__file__).parent.parent.absolute()))
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
            
            # Confirm deletion
            response = input(f"Are you sure you want to delete VRF '{vrf_name}' from fabric '{fabric_name}'? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                print("Deletion cancelled.")
                return False
            
            # Call VRF API for deletion
            success = vrf_api.delete_vrf(fabric_name, vrf_name)
            
            if success:
                print(f"✅ SUCCESS: VRF Delete - {vrf_name}")
                print(f"   VRF '{vrf_name}' has been deleted successfully")
                return True
            else:
                print(f"❌ FAILED: VRF Delete - {vrf_name}")
                print(f"   Failed to delete VRF '{vrf_name}'")
                return False
                
        except Exception as e:
            print(f"❌ Error deleting VRF {vrf_name}: {e}")
            print(f"❌ FAILED: VRF Delete - {vrf_name}")
            print(f"   Failed to delete VRF '{vrf_name}'")
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
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
