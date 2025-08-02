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

# Add the cisco 12.2.2 directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'cisco', '12.2.2'))

# Import all the manager classes from different modules
from modules.fabric import FabricManager
from modules.vrf import VRFManager  
from modules.network import NetworkManager
from modules.switch import SwitchManager
from modules.interface import InterfaceManager
from modules.vpc import VPCManager
import time


fabric_manager = FabricManager()
vrf_manager = VRFManager()
network_manager = NetworkManager()
switch_manager = SwitchManager()
interface_manager = InterfaceManager()
vpc_manager = VPCManager()

FABRIC = "Site3-Test"
MSD = "MSD-Test1"
ISN = "ISN-Test"
SWITCH_1 = "Site1-L3"
SWITCH_2 = "Site2-L3"
SWITCH_LIST = [SWITCH_1, SWITCH_2]
VRF_LIST = ["bluevrf", "bluevrf2"]
NETWORK_LIST = ["bluenet1", "bluenet2", "ExternalNetwork"]
def main():
    # Step 1. Create fabrics
    fabric_manager.create_fabric(FABRIC)
    fabric_manager.create_fabric(MSD)
    fabric_manager.create_fabric(ISN)

    # Step 2. Add switches to fabrics
    for switch in SWITCH_LIST:
        switch_manager.discover_switch(FABRIC, "leaf", switch)
        switch_manager.set_switch_role(FABRIC, "leaf", switch)

    # Step 3. Recalculate
    success = fabric_manager.recalculate_config(FABRIC)
    while not success:
        # Sleep for 5 secs
        time.sleep(30)
        print("Rediscovering Switches...")
        for switch in SWITCH_LIST:
            switch_manager.rediscover_switch(FABRIC, "leaf", switch)
        time.sleep(30)
        success = fabric_manager.recalculate_config(FABRIC)

    print("Recalculation complete.")

    # fabric_manager.deploy_fabric(FABRIC)

    # Step 4. Create VRF
    for vrf in VRF_LIST:
        vrf_manager.create_vrf(FABRIC, vrf)
    
    # Step 5. Attach VRF to switches
    for switch in SWITCH_LIST:
        vrf_manager.attach_vrf(FABRIC, "leaf", switch)

    # Step 6. Create Network
    for network in NETWORK_LIST:
        network_manager.create_network(FABRIC, network)

    # Step 7. Attach Network 
    for switch in SWITCH_LIST:
        network_manager.attach_networks(FABRIC, "leaf", switch)

    # Step 8. Apply interface configurations
    for switch in SWITCH_LIST:
        interface_manager.update_switch_interfaces(FABRIC, "leaf", switch)

    # Step 9. Set switch freeform configs
    for switch in SWITCH_LIST:
        switch_manager.set_switch_freeform(FABRIC, "leaf", switch)

    # Step 10. recalculate
    success = fabric_manager.recalculate_config(FABRIC)
    while not success:
        time.sleep(10)
        success = fabric_manager.recalculate_config(FABRIC)
    
    # Get pending configs
    fabric_manager.get_pending_config(FABRIC)

    # Step 11. Deploy fabric
    # fabric_manager.deploy_fabric(FABRIC)

def delete():
    switch_manager.delete_switch(FABRIC, "leaf", SWITCH_1)
    switch_manager.delete_switch(FABRIC, "leaf", SWITCH_2)

    # fabric_manager.remove_from_msd(MSD, FABRIC)
    # fabric_manager.remove_from_msd(MSD, ISN)
    fabric_manager.delete_fabric(FABRIC)
    fabric_manager.delete_fabric(ISN)
    fabric_manager.delete_fabric(MSD)
    pass

if __name__ == '__main__':
    main()
    # delete()