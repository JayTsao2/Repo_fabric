#!/usr/bin/env python3
"""
Network CLI - Command Line Interface for Network Operations

This script provides command-line access to network management functionality.
"""

import argparse
import sys
from pathlib import Path

# Setup module path
sys.path.append(str(Path(__file__).parent.absolute()))

from modules.network.create_network import NetworkCreator
from modules.network.update_network import NetworkUpdater
from modules.network.delete_network import NetworkDeleter

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Network Management CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a network')
    create_parser.add_argument('fabric_name', help='Name of the fabric')
    create_parser.add_argument('network_name', help='Name of the network')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update a network')
    update_parser.add_argument('fabric_name', help='Name of the fabric')
    update_parser.add_argument('network_name', help='Name of the network')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a network')
    delete_parser.add_argument('fabric_name', help='Name of the fabric')
    delete_parser.add_argument('network_name', help='Name of the network')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'create':
            creator = NetworkCreator()
            success = creator.create_network(args.fabric_name, args.network_name)
            sys.exit(0 if success else 1)
            
        elif args.command == 'update':
            updater = NetworkUpdater()
            success = updater.update_network(args.fabric_name, args.network_name)
            sys.exit(0 if success else 1)
            
        elif args.command == 'delete':
            deleter = NetworkDeleter()
            success = deleter.delete_network(args.fabric_name, args.network_name)
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
