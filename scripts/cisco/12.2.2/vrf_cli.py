#!/usr/bin/env python3
"""
VRF Management CLI

This script provides a simple command-line interface to the VRF module.
It allows you to use the separated create, update, delete functionality for VRFs,
and provides YAML-based VRF attach/detach operations for specific switches.

Example usage:
    python vrf_cli.py create PROD_VRF fabric1
    python vrf_cli.py update PROD_VRF fabric1
    python vrf_cli.py delete PROD_VRF
    python vrf_cli.py attach Site1-Greenfield leaf Site1-L1
    python vrf_cli.py detach Site1-Greenfield leaf Site1-L1
"""

import argparse
import sys
import os

# Add the modules directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

from modules.vrf.create_vrf import VRFCreator
from modules.vrf.update_vrf import VRFUpdater
from modules.vrf.delete_vrf import VRFDeleter
from modules.vrf.attach_vrf import VRFAttachment

def create_vrf_command(args):
    """Handle VRF create command"""
    creator = VRFCreator()
    success = creator.create_vrf(args.vrf_name)
    if success:
        print(f"Successfully created VRF '{args.vrf_name}'")
        return True
    else:
        print(f"Failed to create VRF '{args.vrf_name}'")
        return False

def update_vrf_command(args):
    """Handle VRF update command"""
    updater = VRFUpdater()
    success = updater.update_vrf(args.vrf_name)
    if success:
        print(f"Successfully updated VRF '{args.vrf_name}'")
        return True
    else:
        print(f"Failed to update VRF '{args.vrf_name}'")
        return False

def delete_vrf_command(args):
    """Handle VRF delete command"""
    deleter = VRFDeleter()
    success = deleter.delete_vrf(args.vrf_name)
    if success:
        print(f"Successfully deleted VRF '{args.vrf_name}'")
        return True
    else:
        print(f"Failed to delete VRF '{args.vrf_name}'")
        return False

def attach_vrf_by_name_command(args):
    """Handle VRF attach by name command"""
    attachment = VRFAttachment()
    success = attachment.manage_vrf_by_switch(args.fabric_name, args.switch_role, args.switch_name, operation="attach")
    if success:
        print(f"Successfully attached VRF to switch '{args.switch_name}' in fabric '{args.fabric_name}'")
        return True
    else:
        print(f"Failed to attach VRF to switch '{args.switch_name}' in fabric '{args.fabric_name}'")
        return False

def detach_vrf_by_name_command(args):
    """Handle VRF detach by name command"""
    attachment = VRFAttachment()
    success = attachment.manage_vrf_by_switch(args.fabric_name, args.switch_role, args.switch_name, operation="detach")
    if success:
        print(f"Successfully detached VRF from switch '{args.switch_name}' in fabric '{args.fabric_name}'")
        return True
    else:
        print(f"Failed to detach VRF from switch '{args.switch_name}' in fabric '{args.fabric_name}'")
        return False



def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='VRF Management CLI - Create, update, delete, attach, and detach VRFs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Create VRF:     python vrf_cli.py create PROD_VRF fabric1
  Update VRF:     python vrf_cli.py update PROD_VRF fabric1
  Delete VRF:     python vrf_cli.py delete PROD_VRF
  Attach VRF:     python vrf_cli.py attach Site1-Greenfield leaf Site1-L1
  Detach VRF:     python vrf_cli.py detach Site1-Greenfield leaf Site1-L1
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create VRF command
    create_parser = subparsers.add_parser('create', help='Create a VRF')
    create_parser.add_argument('vrf_name', help='Name of the VRF to create')
    create_parser.add_argument('fabric_name', help='Name of the fabric to create VRF in')
    
    # Update VRF command
    update_parser = subparsers.add_parser('update', help='Update a VRF')
    update_parser.add_argument('vrf_name', help='Name of the VRF to update')
    update_parser.add_argument('fabric_name', help='Name of the fabric to update VRF in')
    
    # Delete VRF command
    delete_parser = subparsers.add_parser('delete', help='Delete a VRF')
    delete_parser.add_argument('vrf_name', help='Name of the VRF to delete')
    
    # Attach VRF by name command (new primary method)
    attach_parser = subparsers.add_parser('attach', help='Attach VRF to a specific switch')
    attach_parser.add_argument('fabric_name', help='Name of the fabric')
    attach_parser.add_argument('switch_role', help='Role of the switch (leaf, spine, border_gateway)')
    attach_parser.add_argument('switch_name', help='Name of the switch')
    
    # Detach VRF by name command (new primary method)
    detach_parser = subparsers.add_parser('detach', help='Detach VRF from a specific switch')
    detach_parser.add_argument('fabric_name', help='Name of the fabric')
    detach_parser.add_argument('switch_role', help='Role of the switch (leaf, spine, border_gateway)')
    detach_parser.add_argument('switch_name', help='Name of the switch')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'create':
            success = create_vrf_command(args)
        elif args.command == 'update':
            success = update_vrf_command(args)
        elif args.command == 'delete':
            success = delete_vrf_command(args)
        elif args.command == 'attach':
            success = attach_vrf_by_name_command(args)
        elif args.command == 'detach':
            success = detach_vrf_by_name_command(args)
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
            success = False
        
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
