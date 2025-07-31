#!/usr/bin/env python3
"""
Fabric Builder - Unified Operations

This module handles both fabric creation and update operations:
- Building/Updating VXLAN EVPN Fabrics
- Building/Updating Multi-Site Domains (MSD)
- Building/Updating Inter-Site Networks (ISN)
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.absolute()))

import api.fabric as fabric_api
from modules.config_utils import validate_configuration_files
from . import FabricType, BaseFabricMethods

class FabricOperations(BaseFabricMethods):
    """Handles unified fabric create and update operations."""
    
    def _execute_fabric_operation(self, fabric_name: str, fabric_type: FabricType, operation: str) -> bool:
        """
        Execute fabric operation (create or update) for any fabric type.
        
        Args:
            fabric_name: Name of the fabric
            fabric_type: Type of fabric to operate on
            operation: Either "create" or "update"
            
        Returns:
            bool: True if successful, False otherwise
        """
        type_names = {
            FabricType.VXLAN_EVPN: "VXLAN EVPN Fabric",
            FabricType.MULTI_SITE_DOMAIN: "Multi-Site Domain",
            FabricType.INTER_SITE_NETWORK: "Inter-Site Network"
        }
        
        type_name = type_names.get(fabric_type, str(fabric_type))

        try:
            # Get configuration and validate files for VXLAN EVPN
            config = self.builder.get_fabric_config(fabric_type, fabric_name)
            print(f"Using config file: {config.config_path}")
            
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
                print(f"Failed to generate payload for {type_name} {operation}")
                return False
            
            # Get freeform paths and add content to payload (for VXLAN_EVPN and ISN)
            if fabric_type in [FabricType.VXLAN_EVPN, FabricType.INTER_SITE_NETWORK]:
                freeform_paths = self.get_freeform_paths(fabric_name, fabric_type)
                
                # Log the freeform config paths being used
                print("Using freeform config files:")
                if freeform_paths.aaa:
                    print(f"  AAA: {freeform_paths.aaa}")
                if freeform_paths.leaf:
                    print(f"  Leaf: {freeform_paths.leaf}")
                if freeform_paths.spine:
                    print(f"  Spine: {freeform_paths.spine}")
                if freeform_paths.intra_links:
                    print(f"  Intra-fabric Links: {freeform_paths.intra_links}")
                if freeform_paths.banner:
                    print(f"  Banner: {freeform_paths.banner}")
                if freeform_paths.fabric:
                    print(f"  Fabric: {freeform_paths.fabric}")
                
                self.payload_generator.add_freeform_content_to_payload(payload_data, template_name, freeform_paths)
            
            # Choose the appropriate API function based on operation
            if operation == "create":
                api_func = lambda: fabric_api.create_fabric(
                    fabric_name=fabric_name_from_file,
                    template_name=template_name,
                    payload_data=payload_data
                )
            else:  # update
                api_func = lambda: fabric_api.update_fabric(
                    fabric_name=fabric_name_from_file,
                    template_name=template_name,
                    payload_data=payload_data
                )
            
            # Execute the fabric operation
            return api_func()
                
        except Exception as e:
            print(f"❌ Error during {operation} operation for fabric {fabric_name}: {e}")
            return False
        
    def create_fabric(self, fabric_name: str) -> bool:
        """
        Generic method to create any type of fabric.
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

        return self._execute_fabric_operation(fabric_name, fabric_type, "create")

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

        return self._execute_fabric_operation(fabric_name, fabric_type, "update")
