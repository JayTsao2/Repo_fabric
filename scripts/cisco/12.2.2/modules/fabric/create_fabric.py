#!/usr/bin/env python3
"""
Fabric Builder - Create Operations

This module handles fabric creation operations:
- Building VXLAN EVPN Fabrics
- Building Multi-Site Domains (MSD)
- Building Inter-Site Networks (ISN)
- Adding child fabrics to MSDs
"""

import sys
from typing import Optional
from pathlib import Path

# Add parent directory to path to access api and config_utils
sys.path.append(str(Path(__file__).parent.parent.absolute()))
import api.fabric as fabric_api
from config_utils import print_build_summary, validate_configuration_files
from . import (
    FabricType, 
    BaseFabricMethods, 
    ChildFabrics,
    extract_child_fabrics_config,
    load_yaml_file
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
                    config.field_mapping_path, config.template_map_path
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
            
            # Apply fabric-specific parameters
            payload_data = self._get_fabric_specific_params(fabric_type, payload_data)
            
            # Get freeform paths and add content to payload (for VXLAN_EVPN and ISN)
            if fabric_type in [FabricType.VXLAN_EVPN, FabricType.INTER_SITE_NETWORK]:
                freeform_paths = self.get_freeform_paths(fabric_name, fabric_type)
                self.payload_generator.add_freeform_content_to_payload(payload_data, template_name, freeform_paths)
            
            print(f"Calling create_fabric API for {type_name}...")
            
            # Call fabric API for creation
            success = fabric_api.create_fabric(
                fabric_name=fabric_name_from_file,
                template_name=template_name,
                payload_data=payload_data
            )
            
            if success:
                print_build_summary(type_name, fabric_name, True, "created")
                return True
            else:
                print_build_summary(type_name, fabric_name, False, "created")
                return False
                
        except Exception as e:
            print(f"❌ Error creating {type_name} {fabric_name}: {e}")
            print_build_summary(type_name, fabric_name, False, "created")
            return False

    def build_vxlan_evpn_fabric(self, fabric_site_name: str) -> bool:
        """Build a VXLAN EVPN fabric configuration."""
        return self._execute_fabric_creation(fabric_site_name, FabricType.VXLAN_EVPN)

    def build_multi_site_domain(self, msd_name: str) -> bool:
        """Build a Multi-Site Domain (MSD) configuration."""
        return self._execute_fabric_creation(msd_name, FabricType.MULTI_SITE_DOMAIN)

    def build_inter_site_network(self, isn_name: str) -> bool:
        """Build an Inter-Site Network (ISN) configuration."""
        return self._execute_fabric_creation(isn_name, FabricType.INTER_SITE_NETWORK)

    def _get_child_fabrics_from_msd_config(self, msd_name: str) -> Optional[ChildFabrics]:
        """Load child fabric information from MSD configuration file."""
        try:
            config = self.builder.get_fabric_config(FabricType.MULTI_SITE_DOMAIN, msd_name)
            fabric_config = load_yaml_file(config.config_path)
            
            if not fabric_config:
                print(f"Failed to load configuration for MSD '{msd_name}'")
                return None
            
            # Extract child fabric information
            child_fabrics_info = extract_child_fabrics_config(fabric_config)
            return ChildFabrics(
                regular_fabrics=child_fabrics_info.get("regular_fabrics", []),
                isn_fabrics=child_fabrics_info.get("isn_fabrics", [])
            )
        except Exception as e:
            print(f"❌ Error loading child fabrics configuration for MSD {msd_name}: {e}")
            return None

    def _execute_msd_child_fabric_operation(self, msd_name: str, operation: str) -> bool:
        """
        Execute add or remove operation for child fabrics in MSD.
        
        Args:
            msd_name: Name of the MSD
            operation: "add" or "remove"
            
        Returns:
            bool: True if successful, False otherwise
        """
        operation_verb = "Adding" if operation == "add" else "Removing"
        operation_preposition = "to" if operation == "add" else "from"
        
        print(f"\n=== {operation_verb} Child Fabrics {operation_preposition} MSD: {msd_name} ===")
        
        # Load child fabric configuration
        child_fabrics = self._get_child_fabrics_from_msd_config(msd_name)
        if not child_fabrics:
            return False
        
        print(f"Found child fabrics: Regular={child_fabrics.regular_fabrics}, ISN={child_fabrics.isn_fabrics}")
        
        if not child_fabrics.get_all_child_fabrics():
            print(f"No child fabrics found in configuration for MSD '{msd_name}'")
            return True
        
        # Execute operation on each child fabric
        all_success = True
        all_child_fabrics = child_fabrics.get_all_child_fabrics()
        
        for child_fabric in all_child_fabrics:
            try:
                print(f"{operation_verb} child fabric '{child_fabric}' {operation_preposition} MSD '{msd_name}'...")
                
                if operation == "add":
                    fabric_api.add_MSD(parent_fabric_name=msd_name, child_fabric_name=child_fabric)
                    print(f"✅ Successfully added '{child_fabric}' to '{msd_name}'")
                else:  # remove
                    fabric_api.remove_MSD(parent_fabric_name=msd_name, child_fabric_name=child_fabric)
                    print(f"✅ Successfully removed '{child_fabric}' from '{msd_name}'")
                    
            except Exception as e:
                print(f"❌ Failed to {operation} '{child_fabric}' {operation_preposition} '{msd_name}': {e}")
                all_success = False
        
        if all_success:
            action_past = "added to" if operation == "add" else "removed from"
            print(f"✅ All child fabrics successfully {action_past} MSD '{msd_name}'")
        else:
            action_past = "be added to" if operation == "add" else "be removed from"
            print(f"⚠️  Some child fabrics failed to {action_past} MSD '{msd_name}'")
        
        return all_success

    def add_child_fabrics_to_msd(self, msd_name: str) -> bool:
        """Add child fabrics to an MSD based on its configuration file."""
        return self._execute_msd_child_fabric_operation(msd_name, "add")

    def remove_child_fabrics_from_msd(self, msd_name: str) -> bool:
        """Remove child fabrics from an MSD based on its configuration file."""
        return self._execute_msd_child_fabric_operation(msd_name, "remove")

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
        if not fabric_type:
            print(f"❌ Cannot determine fabric type for: {fabric_name}")
            return False
        
        print(f"Building fabric '{fabric_name}' of type: {fabric_type}")
        
        if fabric_type == FabricType.VXLAN_EVPN:
            return self.build_vxlan_evpn_fabric(fabric_name)
        elif fabric_type == FabricType.MULTI_SITE_DOMAIN:
            return self.build_multi_site_domain(fabric_name)
        elif fabric_type == FabricType.INTER_SITE_NETWORK:
            return self.build_inter_site_network(fabric_name)
        else:
            print(f"❌ Unsupported fabric type: {fabric_type}")
            return False


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
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
