#!/usr/bin/env python3
"""
Fabric Management CLI

This script provides a simple command-line interface to the fabric module.
It demonstrates how to use the separated create, update, and delete functionality.

Usage:
    python fabric_cli.py create <fabric_name>
    python fabric_cli.py update <fabric_name>
    python fabric_cli.py delete <fabric_name>
"""

import sys
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

def main():
    parser = argparse.ArgumentParser(
        description="Fabric Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fabric_cli.py create Site3-Test     # Create a specific fabric
  python fabric_cli.py update MSD-Test_15    # Update a specific fabric
  python fabric_cli.py delete ISN-Test       # Delete a specific fabric
"""
    )
    
    parser.add_argument('command', 
                       choices=['create', 'update', 'delete'],
                       help='Command to execute')
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
            
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
