#!/usr/bin/env python3
"""
Switch CLI - Command Line Interface for Switch Operations

This script provides command-line access to switch management functionality
using the unified SwitchManager class.

Usage:
    python switch_cli.py discover {fabric} {role} {switch} [--preserve]
    python switch_cli.py delete {fabric} {role} {switch}
    python switch_cli.py set-role {switch}
    python switch_cli.py change-ip {fabric} {role} {switch} {original-ip}/{mask} {new-ip}/{mask}
    python switch_cli.py set-freeform {fabric} {role} {switch}
    
Note: set-freeform creates a freeform policy for the switch using NDFC Policy API
"""

import argparse
import sys
from pathlib import Path

# Setup module path
sys.path.append(str(Path(__file__).parent.absolute()))

from modules.switch import SwitchManager

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Switch Management CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Discover a switch')
    discover_parser.add_argument('fabric_name', help='Name of the fabric')
    discover_parser.add_argument('role', help='Role of the switch (leaf, spine, border, etc.)')
    discover_parser.add_argument('switch_name', help='Name of the switch')
    discover_parser.add_argument('--preserve', action='store_true', 
                                help='Preserve existing configuration (default: False)')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a switch')
    delete_parser.add_argument('fabric_name', help='Name of the fabric')
    delete_parser.add_argument('role', help='Role of the switch (leaf, spine, border, etc.)')
    delete_parser.add_argument('switch_name', help='Name of the switch')
    
    # Set-role command
    setrole_parser = subparsers.add_parser('set-role', help='Set switch role')
    setrole_parser.add_argument('switch_name', help='Name of the switch')
    
    # Change-ip command
    changeip_parser = subparsers.add_parser('change-ip', help='Change switch management IP')
    changeip_parser.add_argument('fabric_name', help='Name of the fabric')
    changeip_parser.add_argument('role', help='Role of the switch (leaf, spine, border, etc.)')
    changeip_parser.add_argument('switch_name', help='Name of the switch')
    changeip_parser.add_argument('original_ip', help='Original IP address with mask (e.g., 192.168.1.1/24)')
    changeip_parser.add_argument('new_ip', help='New IP address with mask (e.g., 192.168.1.2/24)')
    
    # Set-freeform command
    setfreeform_parser = subparsers.add_parser('set-freeform', help='Create freeform policy for switch')
    setfreeform_parser.add_argument('fabric_name', help='Name of the fabric')
    setfreeform_parser.add_argument('role', help='Role of the switch (leaf, spine, border, etc.)')
    setfreeform_parser.add_argument('switch_name', help='Name of the switch')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        # Create SwitchManager instance
        switch_manager = SwitchManager()
        
        if args.command == 'discover':
            # Discover switch with preserve config option
            success = switch_manager.discover_switch(
                args.fabric_name, 
                args.role, 
                args.switch_name,
                preserve_config=args.preserve
            )
        elif args.command == 'delete':
            # Delete switch
            success = switch_manager.delete_switch(
                args.fabric_name, 
                args.role, 
                args.switch_name
            )
        elif args.command == 'set-role':
            # Set switch role
            success = switch_manager.set_switch_role_by_name(args.switch_name)
        elif args.command == 'change-ip':
            # Change switch IP
            success = switch_manager.change_switch_ip(
                args.fabric_name,
                args.role,
                args.switch_name,
                args.original_ip,
                args.new_ip
            )
        elif args.command == 'set-freeform':
            # Apply freeform configuration
            success = switch_manager.set_switch_freeform(
                args.fabric_name,
                args.role,
                args.switch_name
            )
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
