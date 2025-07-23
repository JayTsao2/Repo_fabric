#!/usr/bin/env python3
"""
Fabric Management CLI

This script provides a simple command-line interface to the fabric module.
It demonstrates how to use the separated create, update, delete, and MSD functionality.

Usage:
    python fabric_cli.py create <fabric_name>
    python fabric_cli.py update <fabric_name>
    python fabric_cli.py delete <fabric_name>
    python fabric_cli.py add-msd <parent_msd> <child_fabric>
    python fabric_cli.py remove-msd <parent_msd> <child_fabric>
"""

import sys
from pathlib import Path

# Add current directory to path to access modules
sys.path.append(str(Path(__file__).parent.absolute()))

import argparse
from modules.fabric.create_fabric import FabricCreator
from modules.fabric.update_fabric import FabricUpdater
from modules.fabric.delete_fabric import FabricDeleter

def create_fabric_command(fabric_name: str):
    """Handle fabric creation command."""
    creator = FabricCreator()
    print(f"🏗️  Creating fabric: {fabric_name}")
    success = creator.build_fabric(fabric_name)
    return 0 if success else 1

def update_fabric_command(fabric_name: str):
    """Handle fabric update command."""
    updater = FabricUpdater()
    print(f"🔧  Updating fabric: {fabric_name}")
    success = updater.update_fabric(fabric_name)
    return 0 if success else 1

def delete_fabric_command(fabric_name: str):
    """Handle fabric deletion command."""
    deleter = FabricDeleter()
    print(f"🗑️  Deleting fabric: {fabric_name}")
    # Add confirmation prompt for safety
    confirm = input(f"Are you sure you want to delete fabric '{fabric_name}'? (y/N): ")
    if confirm.lower() not in ['y', 'yes']:
        print("❌ Delete operation cancelled by user")
        return 0
        
    success = deleter.delete_fabric(fabric_name)
    return 0 if success else 1

def add_msd_command(parent_fabric: str, child_fabric: str):
    """Handle adding child fabric to MSD command."""
    creator = FabricCreator()
    print(f"🔗  Adding child fabric '{child_fabric}' to MSD '{parent_fabric}'")
    success = creator.link_fabrics(parent_fabric, child_fabric)
    return 0 if success else 1

def remove_msd_command(parent_fabric: str, child_fabric: str):
    """Handle removing specific child fabric from MSD command."""
    creator = FabricCreator()
    print(f"🔓  Removing child fabric '{child_fabric}' from MSD '{parent_fabric}'")
    # Add confirmation prompt for safety
    confirm = input(f"Are you sure you want to remove '{child_fabric}' from MSD '{parent_fabric}'? (y/N): ")
    if confirm.lower() not in ['y', 'yes']:
        print("❌ Remove operation cancelled by user")
        return 0
        
    success = creator.unlink_fabrics(parent_fabric, child_fabric)
    return 0 if success else 1

def main():
    parser = argparse.ArgumentParser(
        description="Fabric Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fabric_cli.py create Site3-Test                     # Create a specific fabric
  python fabric_cli.py update MSD-Test_15                    # Update a specific fabric
  python fabric_cli.py delete ISN-Test                       # Delete a specific fabric
  python fabric_cli.py add-msd MSD-Test Site3-Test          # Add child fabric to MSD
  python fabric_cli.py remove-msd MSD-Test Site3-Test       # Remove specific child fabric from MSD
"""
    )
    
    parser.add_argument('command', 
                       choices=['create', 'update', 'delete', 'add-msd', 'remove-msd'],
                       help='Command to execute')
    
    # Handle different argument patterns for different commands
    if len(sys.argv) > 1 and sys.argv[1] in ['add-msd', 'remove-msd']:
        parser.add_argument('parent_fabric', 
                           help='Parent MSD fabric name')
        parser.add_argument('child_fabric',
                           help='Child fabric name to add/remove to/from MSD')
    else:
        parser.add_argument('fabric_name', 
                           help='Name of the fabric to create/update/delete')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'create':
            return create_fabric_command(args.fabric_name)
            
        elif args.command == 'update':
            return update_fabric_command(args.fabric_name)
            
        elif args.command == 'delete':
            return delete_fabric_command(args.fabric_name)
            
        elif args.command == 'add-msd':
            return add_msd_command(args.parent_fabric, args.child_fabric)
            
        elif args.command == 'remove-msd':
            return remove_msd_command(args.parent_fabric, args.child_fabric)
            
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
