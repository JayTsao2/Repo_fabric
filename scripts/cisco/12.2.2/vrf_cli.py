#!/usr/bin/env python3
"""
VRF Management CLI

This script provides a simple command-line interface to the VRF module.
It demonstrates how to use the separated create, update, delete functionality for VRFs,
and provides YAML-based VRF attach/detach operations.

Usage:
    python vrf_cli.py create <vrf_name>
    python vrf_cli.py update <vrf_name>
    python vrf_cli.py delete <vrf_name>
    python vrf_cli.py attach-vlan <vlan_id> <fabric_name>
    python vrf_cli.py detach-vlan <vlan_id> <fabric_name>
    python vrf_cli.py list-fabrics
    python vrf_cli.py list-vrfs [--fabric <fabric_name>]
"""

import sys
from pathlib import Path

# Add current directory to path to access modules
sys.path.append(str(Path(__file__).parent.absolute()))

import argparse
from modules.vrf.create_vrf import VRFCreator
from modules.vrf.attach_vrf import VRFAttachment
from modules.vrf.update_vrf import VRFUpdater
from modules.vrf.delete_vrf import VRFDeleter

def create_vrf_command(vrf_name: str):
    """Handle VRF creation command."""
    creator = VRFCreator()
    print(f"🏗️  Creating VRF: {vrf_name}")
    success = creator.create_vrf(vrf_name)
    return 0 if success else 1

def update_vrf_command(vrf_name: str):
    """Handle VRF update command."""
    updater = VRFUpdater()
    print(f"🔧  Updating VRF: {vrf_name}")
    success = updater.update_vrf(vrf_name)
    return 0 if success else 1

def delete_vrf_command(vrf_name: str):
    """Handle VRF deletion command."""
    deleter = VRFDeleter()
    print(f"🗑️  Deleting VRF: {vrf_name}")
    success = deleter.delete_vrf(vrf_name)
    return 0 if success else 1

def list_fabrics_command():
    """Handle listing available fabrics."""
    from modules.vrf import VRFBuilder
    builder = VRFBuilder()
    fabrics = builder.get_all_fabrics()
    if fabrics:
        print("📋 Available fabrics with VRF configurations:")
        for fabric in fabrics:
            print(f"  - {fabric}")
    else:
        print("No fabrics found with VRF configurations.")
    return 0

def list_vrfs_command(fabric_name: str = None):
    """Handle listing VRFs for a specific fabric."""
    from modules.vrf import VRFBuilder
    builder = VRFBuilder()
    
    if fabric_name:
        vrfs = builder.get_fabric_vrfs(fabric_name)
        if vrfs:
            print(f"📋 VRFs in fabric '{fabric_name}':")
            for vrf in vrfs:
                print(f"  - {vrf.get('VRF Name')} (ID: {vrf.get('VRF ID')}, VLAN: {vrf.get('VLAN ID')})")
        else:
            print(f"No VRFs found for fabric '{fabric_name}'.")
    else:
        # List all VRFs grouped by fabric
        fabrics = builder.get_all_fabrics()
        for fabric in fabrics:
            vrfs = builder.get_fabric_vrfs(fabric)
            print(f"📋 VRFs in fabric '{fabric}':")
            for vrf in vrfs:
                print(f"  - {vrf.get('VRF Name')} (ID: {vrf.get('VRF ID')}, VLAN: {vrf.get('VLAN ID')})")
            print()
    return 0

def attach_vrf_by_vlan_command(vlan_id: int, fabric_name: str):
    """Handle VRF attachment by VLAN ID to matching switches."""
    from modules.vrf.attach_vrf import VRFAttachment
    
    try:
        attachment = VRFAttachment()
        print(f"🔗 Attaching VRF with VLAN {vlan_id} to switches in fabric {fabric_name}")
        success = attachment.attach_vrf_by_vlan(vlan_id, fabric_name)
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

def detach_vrf_by_vlan_command(vlan_id: int, fabric_name: str):
    """Handle VRF detachment by VLAN ID from matching switches."""
    from modules.vrf.attach_vrf import VRFAttachment
    
    try:
        attachment = VRFAttachment()
        print(f"🔌 Detaching VRF with VLAN {vlan_id} from switches in fabric {fabric_name}")
        success = attachment.detach_vrf_by_vlan(vlan_id, fabric_name)
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

def main():
    parser = argparse.ArgumentParser(
        description="VRF Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python vrf_cli.py create bluevrf                          # Create VRF (fabric extracted from config)
  python vrf_cli.py update bluevrf                          # Update VRF (fabric extracted from config)
  python vrf_cli.py delete bluevrf                          # Delete VRF (fabric extracted from config)
  python vrf_cli.py attach-vlan 2300 Site1-Greenfield      # Attach VRF by VLAN ID to matching switches
  python vrf_cli.py detach-vlan 2300 Site1-Greenfield      # Detach VRF by VLAN ID from matching switches
  python vrf_cli.py list-fabrics                            # List all available fabrics
  python vrf_cli.py list-vrfs                               # List all VRFs grouped by fabric
  python vrf_cli.py list-vrfs --fabric Site1-Greenfield    # List VRFs for specific fabric
"""
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a VRF')
    create_parser.add_argument('vrf_name', help='Name of the VRF to create')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update a VRF')
    update_parser.add_argument('vrf_name', help='Name of the VRF to update')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a VRF')
    delete_parser.add_argument('vrf_name', help='Name of the VRF to delete')
    
    # List fabrics command
    list_fabrics_parser = subparsers.add_parser('list-fabrics', help='List all available fabrics')
    
    # List VRFs command
    list_vrfs_parser = subparsers.add_parser('list-vrfs', help='List VRFs')
    list_vrfs_parser.add_argument('--fabric', help='Filter VRFs by fabric name')
    
    # Attach VRF by VLAN command (YAML-based)
    attach_vlan_parser = subparsers.add_parser('attach-vlan', help='Attach VRF by VLAN ID to matching switches')
    attach_vlan_parser.add_argument('vlan_id', type=int, help='VLAN ID to match in switch configurations')
    attach_vlan_parser.add_argument('fabric_name', help='Name of the fabric to search for switches')
    
    # Detach VRF by VLAN command (YAML-based)
    detach_vlan_parser = subparsers.add_parser('detach-vlan', help='Detach VRF by VLAN ID from matching switches')
    detach_vlan_parser.add_argument('vlan_id', type=int, help='VLAN ID to match in switch configurations')
    detach_vlan_parser.add_argument('fabric_name', help='Name of the fabric to search for switches')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'create':
            return create_vrf_command(args.vrf_name)
            
        elif args.command == 'update':
            return update_vrf_command(args.vrf_name)
            
        elif args.command == 'delete':
            return delete_vrf_command(args.vrf_name)
            
        elif args.command == 'list-fabrics':
            return list_fabrics_command()
            
        elif args.command == 'list-vrfs':
            return list_vrfs_command(args.fabric)
            
        elif args.command == 'attach-vlan':
            return attach_vrf_by_vlan_command(args.vlan_id, args.fabric_name)
            
        elif args.command == 'detach-vlan':
            return detach_vrf_by_vlan_command(args.vlan_id, args.fabric_name)
            
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
