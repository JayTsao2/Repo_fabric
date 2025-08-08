#!/usr/bin/env python3
"""
Build Script - Import all NDFC modules for fabric automation

This script automatically loads the NDFC management IP from fabric_builder.yaml
and provides access to all cisco 12.2.2 automation modules.

Configuration:
- NDFC IP is read from: network_configs/fabric_builder.yaml
- Falls back to default if config file is not found
"""
import sys
import os
import json
import time

# Add the cisco 12.2.2 directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'cisco', '12.2.2'))

# Import all the manager classes from different modules
from modules.fabric import FabricManager
from modules.vrf import VRFManager  
from modules.network import NetworkManager
from modules.switch import SwitchManager
from modules.interface import InterfaceManager
from modules.vpc import VPCManager


class FabricBuilder:
    """
    Main class for building and managing NDFC fabric configurations.
    """
    
    def __init__(self):
        """Initialize all manager instances."""
        self.fabric_manager = FabricManager()
        self.vrf_manager = VRFManager()
        self.network_manager = NetworkManager()
        self.switch_manager = SwitchManager()
        self.interface_manager = InterfaceManager()
        self.vpc_manager = VPCManager()

    def banner(self):
        """Print a banner for the builder."""
        print("=========================================================")
        print("        NDFC Fabric Builder - Version 12.2.2")
        print("=========================================================")

    def get_root_dir(self):
        """
        Get the root directory of the repository.
        This is used to ensure that the script runs from the correct directory.
        """
        # Get current file's directory and navigate up to root
        current_dir = os.path.dirname(os.path.abspath(__file__))  # 12.2.2
        cisco_dir = os.path.dirname(current_dir)                  # cisco
        scripts_dir = os.path.dirname(cisco_dir)                  # scripts
        root_dir = os.path.dirname(scripts_dir)                   # Repo_fabric
        return root_dir

    def get_MSD_list(self):
        """
        Get the list of MSDs from the configuration.
        """
        msds = []
        msd_dir = os.path.join(self.get_root_dir(), 'network_configs', '1_vxlan_evpn', 'multisite_deployment')
        if os.path.exists(msd_dir):
            for msd_file in os.listdir(msd_dir):
                if msd_file.endswith('.yaml'):
                    msds.append(msd_file[:-5])  # Remove .yaml extension
        return msds

    def get_ISN_list(self):
        """
        Get the list of ISNs from the configuration.
        """
        isn_list = []
        isn_dir = os.path.join(self.get_root_dir(), 'network_configs', '1_vxlan_evpn', 'inter-site_network')
        if os.path.exists(isn_dir):
            for isn_file in os.listdir(isn_dir):
                if isn_file.endswith('.yaml'):
                    isn_list.append(isn_file[:-5])  # Remove .yaml extension
        return isn_list

    def get_switch_list(self):
        """
        Get the list of switches from the configuration.
        Returns a nested dictionary with fabric -> role -> [nodes] structure.
        """
        switches = {}
        switch_dir = os.path.join(self.get_root_dir(), 'network_configs', '3_node')
        
        if os.path.exists(switch_dir):
            # Iterate through fabrics
            for fabric_name in os.listdir(switch_dir):
                fabric_path = os.path.join(switch_dir, fabric_name)
                if os.path.isdir(fabric_path):
                    switches[fabric_name] = {}
                    
                    # Iterate through roles within each fabric
                    for role_name in os.listdir(fabric_path):
                        if role_name == "vpc":
                            # Skip VPC directory since it is not a role
                            continue
                        role_path = os.path.join(fabric_path, role_name)
                        if os.path.isdir(role_path):
                            switches[fabric_name][role_name] = []
                            
                            # Iterate through node files within each role
                            for node_file in os.listdir(role_path):
                                if node_file.endswith('.yaml'):
                                    node_name = node_file[:-5]  # Remove .yaml extension
                                    switches[fabric_name][role_name].append(node_name)
        
        return switches

    def build(self):
        """
        Build the fabric configuration.
        """
        self.banner()
        # Get the structured switch data
        all_switches_data = self.get_switch_list()
        all_msd_list = self.get_MSD_list()
        all_isn_list = self.get_ISN_list()
        
        # Filter to only use Site3-Test fabric
        switches_data = {}
        if "Site3-Test" in all_switches_data:
            switches_data["Site3-Test"] = all_switches_data["Site3-Test"]
        msd_list = [msd for msd in all_msd_list if msd.startswith("MSD-Test")]
        isn_list = [isn for isn in all_isn_list if isn.startswith("ISN-Test")]

        # Step 1. Create fabrics
        for fabric_name in switches_data.keys():
            self.fabric_manager.create_fabric(fabric_name)
        
        for msd in msd_list:
            self.fabric_manager.create_fabric(msd)
            
        for isn in isn_list:
            self.fabric_manager.create_fabric(isn)

        # Step 2. Add switches to fabrics
        for fabric_name, roles in switches_data.items():
            for role_name, switches in roles.items():
                for switch in switches:
                    self.switch_manager.discover_switch(fabric_name, role_name, switch)
                    self.switch_manager.set_switch_role(fabric_name, role_name, switch)

        # Step 3. Recalculate for each fabric
        for fabric_name in switches_data.keys():
            success = self.fabric_manager.recalculate_config(fabric_name)
            while not success:
                # Sleep for 30 secs
                time.sleep(30)
                print(f"Rediscovering Switches for fabric {fabric_name}...")
                for role_name, switches in switches_data[fabric_name].items():
                    for switch in switches:
                        self.switch_manager.rediscover_switch(fabric_name, role_name, switch)
                time.sleep(30)
                success = self.fabric_manager.recalculate_config(fabric_name)

            print(f"Recalculation complete for fabric {fabric_name}.")

        # Step 4. Update VRFs (delete unwanted, update existing, create missing)
        for fabric_name in switches_data.keys():
            self.vrf_manager.sync(fabric_name)
        
        # Step 5. Attach VRF to switches
        for fabric_name, roles in switches_data.items():
            for role_name, switches in roles.items():
                for switch in switches:
                    self.vrf_manager.sync_attachments(fabric_name, role_name, switch)

        # Step 6. Update Networks (delete unwanted, update existing, create missing)
        for fabric_name in switches_data.keys():
            self.network_manager.sync(fabric_name)

        # Step 7. Attach Network 
        for fabric_name, roles in switches_data.items():
            for role_name, switches in roles.items():
                for switch in switches:
                    self.network_manager.attach_networks(fabric_name, role_name, switch)

        # Step 8. Apply interface configurations
        for fabric_name, roles in switches_data.items():
            for role_name, switches in roles.items():
                for switch in switches:
                    self.interface_manager.update_switch_interfaces(fabric_name, role_name, switch)

        # Step 9. Create VPC pairs for each fabric
        for fabric_name in switches_data.keys():
            self.vpc_manager.create_vpc_pairs(fabric_name)

        # Step 10. Set switch freeform configs
        for fabric_name, roles in switches_data.items():
            for role_name, switches in roles.items():
                for switch in switches:
                    self.switch_manager.set_switch_freeform(fabric_name, role_name, switch)

        # Step 11. Add fabrics to MSD
        if msd_list and switches_data:
            for msd in msd_list:
                for fabric_name in switches_data.keys():
                    self.fabric_manager.add_to_msd(msd, fabric_name)
                for isn in isn_list:
                    self.fabric_manager.add_to_msd(msd, isn)

        # Step 12. Final recalculate for each fabric
        for fabric_name in switches_data.keys():
            success = self.fabric_manager.recalculate_config(fabric_name)
            while not success:
                time.sleep(10)
                success = self.fabric_manager.recalculate_config(fabric_name)
        
            # Get pending configs
            self.fabric_manager.get_pending_config(fabric_name)

        # Step 13. Deploy fabric
        # for fabric_name in switches_data.keys():
        #     self.fabric_manager.deploy_fabric(fabric_name)

    def delete(self):
        """
        Delete fabric configurations using dynamic data.
        """
        # Get the structured data
        switches_data = self.get_switch_list()
        msd_list = self.get_MSD_list()
        isn_list = self.get_ISN_list()
        
        # Filter to only use Site3-Test fabric (same as build)
        filtered_switches_data = {}
        if "Site3-Test" in switches_data:
            filtered_switches_data["Site3-Test"] = switches_data["Site3-Test"]
        filtered_msd_list = [msd for msd in msd_list if msd.startswith("MSD-Test")]
        filtered_isn_list = [isn for isn in isn_list if isn.startswith("ISN-Test")]
        
        # Delete all switches from all fabrics
        for fabric_name, roles in filtered_switches_data.items():
            for role_name, switches in roles.items():
                for switch in switches:
                    self.switch_manager.delete_switch(fabric_name, role_name, switch)

        # Remove fabrics from MSDs
        if filtered_msd_list and filtered_switches_data:
            for msd in filtered_msd_list:
                for fabric_name in filtered_switches_data.keys():
                    self.fabric_manager.remove_from_msd(msd, fabric_name)
                for isn in filtered_isn_list:
                    self.fabric_manager.remove_from_msd(msd, isn)

        # Delete all fabrics
        for fabric_name in filtered_switches_data.keys():
            self.fabric_manager.delete_fabric(fabric_name)
        
        # Delete ISN fabrics
        for isn in filtered_isn_list:
            self.fabric_manager.delete_fabric(isn)
        
        # Delete MSD fabrics
        for msd in filtered_msd_list:
            self.fabric_manager.delete_fabric(msd)


if __name__ == '__main__':
    builder = FabricBuilder()
    # builder.build()
    # builder.delete()
    pass