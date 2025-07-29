#!/usr/bin/env python3
"""
Fabric Builder - Create Operations

This module handles fabric creation operations:
- Building VXLAN EVPN Fabrics
- Building Multi-Site Domains (MSD)
- Building Inter-Site Networks (ISN)
- Adding child fabrics to MSDs
"""

from modules.common_utils import setup_module_path, OperationExecutor
setup_module_path(__file__)

import api.fabric as fabric_api
from modules.config_utils import validate_configuration_files
from . import (
    FabricType, 
    BaseFabricMethods, 
)

class FabricCreator(BaseFabricMethods):
    """Handles fabric creation operations."""
    
    def _execute_fabric_creation(self, fabric_name: str, fabric_type: FabricType) -> bool:
        """
        Execute fabric creation for any fabric type.
        
        Args:
            fabric_name: Name of the fabric
            fabric_type: Type of fabric to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        type_names = {
            FabricType.VXLAN_EVPN: "VXLAN EVPN Fabric",
            FabricType.MULTI_SITE_DOMAIN: "Multi-Site Domain",
            FabricType.INTER_SITE_NETWORK: "Inter-Site Network"
        }
        
        type_name = type_names.get(fabric_type, str(fabric_type))
        print(f"\n=== Building {type_name}: {fabric_name} ===")
        
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
                print(f"Failed to generate payload for {type_name} creation")
                return False
            
            # Get freeform paths and add content to payload (for VXLAN_EVPN and ISN)
            if fabric_type in [FabricType.VXLAN_EVPN, FabricType.INTER_SITE_NETWORK]:
                freeform_paths = self.get_freeform_paths(fabric_name, fabric_type)
                self.payload_generator.add_freeform_content_to_payload(payload_data, template_name, freeform_paths)
            
            print(f"Calling create_fabric API for {type_name}...")
            
            # Call fabric API for creation
            # Execute the fabric creation operation
            return OperationExecutor.execute_operation(
                operation_name="create",
                resource_name=fabric_name,
                resource_type=type_name,
                operation_func=lambda: fabric_api.create_fabric(
                    fabric_name=fabric_name_from_file,
                    template_name=template_name,
                    payload_data=payload_data
                )
            )
                
        except Exception as e:
            from modules.common_utils import MessageFormatter
            MessageFormatter.error("create", fabric_name, e, type_name)
            return False

    def link_fabrics(self, parent_fabric: str, child_fabric: str) -> bool:
        """Link a child fabric to a parent fabric."""
        print(f"\n=== Linking {child_fabric} to {parent_fabric} ===")
        
        try:
            fabric_api.add_MSD(parent_fabric_name=parent_fabric, child_fabric_name=child_fabric)
            print(f"✅ Successfully linked {child_fabric} to {parent_fabric}")
            return True
        except Exception as e:
            print(f"❌ Error linking fabrics: {e}")
            return False

    def unlink_fabrics(self, parent_fabric: str, child_fabric: str) -> bool:
        """Unlink a child fabric from a parent fabric."""
        print(f"\n=== Unlinking {child_fabric} from {parent_fabric} ===")
        
        try:
            fabric_api.remove_MSD(parent_fabric_name=parent_fabric, child_fabric_name=child_fabric)
            print(f"✅ Successfully unlinked {child_fabric} from {parent_fabric}")
            return True
        except Exception as e:
            print(f"❌ Error unlinking fabrics: {e}")
            return False

    def build_fabric(self, fabric_name: str) -> bool:
        """
        Generic method to build any type of fabric.
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

        return self._execute_fabric_creation(fabric_name, fabric_type)


def main():
    """
    Main function for fabric creation operations.
    """
    fabric_creator = FabricCreator()
    
    print("🏗️  Fabric Creator - Network Fabric Creation Tool")
    print("=" * 60)
    
    # Configuration - Update these values as needed
    fabric_site_to_build = "Site3-Test"
    msd_to_build = "MSD-Test_15"
    isn_to_build = "ISN-Test"
    
    # --- Generic Build Method (reads fabric type from YAML files) ---
    
    # Build VXLAN EVPN fabric using generic method (fabric type determined from YAML)
    success = fabric_creator.build_fabric(fabric_site_to_build)
    if not success:
        print(f"Failed to build fabric: {fabric_site_to_build}")
        return 1
    
    # Build Multi-Site Domain using generic method (fabric type determined from YAML)
    success = fabric_creator.build_fabric(msd_to_build)
    if not success:
        print(f"Failed to build fabric: {msd_to_build}")
        return 1
    
    # Build Inter-Site Network using generic method (fabric type determined from YAML)
    success = fabric_creator.build_fabric(isn_to_build)
    if not success:
        print(f"Failed to build fabric: {isn_to_build}")
        return 1

    # --- Add Child Fabrics to MSD ---
    # Uncomment to add child fabrics to the MSD
    # success = fabric_creator.add_child_fabrics_to_msd(msd_to_build)
    # if not success:
    #     print(f"Failed to add child fabrics to MSD: {msd_to_build}")
    #     return 1
    
    print("\n🎉 Fabric creation process completed successfully!")
    return 0


if __name__ == "__main__":
    from modules.common_utils import create_main_function_wrapper
    main_wrapper = create_main_function_wrapper("Fabric Creator", main)
    main_wrapper()
