#!/usr/bin/env python3
"""
Fabric Builder - Update Operations

This module handles fabric update operations:
- Updating VXLAN EVPN Fabrics
- Updating Multi-Site Domains (MSD)
- Updating Inter-Site Networks (ISN)
"""

import sys
from pathlib import Path

# Add parent directory to path to access api and config_utils
sys.path.append(str(Path(__file__).parent.parent.absolute()))
import api.fabric as fabric_api
from config_utils import print_build_summary, validate_configuration_files
from . import FabricType, BaseFabricMethods

class FabricUpdater(BaseFabricMethods):
    """Handles fabric update operations."""
    
    def _execute_fabric_update(self, fabric_name: str, fabric_type: FabricType) -> bool:
        """
        Execute fabric update for any fabric type.
        
        Args:
            fabric_name: Name of the fabric
            fabric_type: Type of fabric to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        type_names = {
            FabricType.VXLAN_EVPN: "VXLAN EVPN Fabric",
            FabricType.MULTI_SITE_DOMAIN: "Multi-Site Domain",
            FabricType.INTER_SITE_NETWORK: "Inter-Site Network"
        }
        
        type_name = type_names.get(fabric_type, str(fabric_type))
        print(f"\n=== Updating {type_name}: {fabric_name} ===")
        
        try:
            # Get configuration and validate files for VXLAN EVPN
            config = self.builder.get_fabric_config(fabric_type, fabric_name)
            
            if fabric_type == FabricType.VXLAN_EVPN:
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
            
            # Generate payload
            payload_data, template_name, fabric_name_from_file = self.payload_generator.prepare_fabric_payload(config)
            if not payload_data or not template_name or not fabric_name_from_file:
                print(f"Failed to generate payload for {type_name} update")
                return False
            
            # Get freeform paths and add content to payload (for VXLAN_EVPN and ISN)
            if fabric_type in [FabricType.VXLAN_EVPN, FabricType.INTER_SITE_NETWORK]:
                freeform_paths = self.get_freeform_paths(fabric_name, fabric_type)
                self.payload_generator.add_freeform_content_to_payload(payload_data, template_name, freeform_paths)
            
            print(f"Calling update_fabric API for {type_name}...")
            
            # Call fabric API for update
            success = fabric_api.update_fabric(
                fabric_name=fabric_name_from_file,
                template_name=template_name,
                payload_data=payload_data
            )
            
            if success:
                print_build_summary(f"{type_name} Update", fabric_name, True, "updated")
                return True
            else:
                print_build_summary(f"{type_name} Update", fabric_name, False, "updated")
                return False
                
        except Exception as e:
            print(f"❌ Error updating {type_name} {fabric_name}: {e}")
            print_build_summary(f"{type_name} Update", fabric_name, False, "updated")
            return False

    def update_fabric(self, fabric_name: str) -> bool:
        """
        Generic method to update any type of fabric.
        Determines the fabric type from the YAML configuration file.
        
        Args:
            fabric_name: Name of the fabric configuration file (without .yaml extension)
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Determine fabric type from the configuration file
        fabric_type = self._determine_fabric_type_from_file(fabric_name)

        # Check if the fabric type is supported
        if not fabric_type or fabric_type not in FabricType:
            print(f"❌ Unsupported fabric type: {fabric_type}")
            return False

        return self._execute_fabric_update(fabric_name, fabric_type)


def main():
    """
    Main function for fabric update operations.
    """
    fabric_updater = FabricUpdater()
    
    print("🔧  Fabric Updater - Network Fabric Update Tool")
    print("=" * 60)
    
    # Configuration - Update these values as needed
    fabric_site_to_update = "Site3-Test"
    msd_to_update = "MSD-Test_15"
    isn_to_update = "ISN-Test"
    
    # --- Update Existing Fabrics ---
    
    # Update VXLAN EVPN fabric (fabric type determined from YAML)
    success = fabric_updater.update_fabric(fabric_site_to_update)
    if not success:
        print(f"Failed to update fabric: {fabric_site_to_update}")
        return 1
    
    # Update Multi-Site Domain (fabric type determined from YAML)
    success = fabric_updater.update_fabric(msd_to_update)
    if not success:
        print(f"Failed to update fabric: {msd_to_update}")
        return 1
    
    # Update Inter-Site Network (fabric type determined from YAML)
    success = fabric_updater.update_fabric(isn_to_update)
    if not success:
        print(f"Failed to update fabric: {isn_to_update}")
        return 1
    
    print("\n🎉 Fabric update process completed successfully!")
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
