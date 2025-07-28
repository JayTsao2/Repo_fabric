#!/usr/bin/env python3
"""
Interface CLI - Command Line Interface for Interface Operations

This script provides command-line access to interface management functionality
using the unified InterfaceManager class.
"""

import argparse
import sys
from pathlib import Path

# Setup module path
sys.path.append(str(Path(__file__).parent.absolute()))

from modules.interface import InterfaceManager

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Interface Management CLI')
    parser.add_argument('fabric_name', help='Name of the fabric')
    parser.add_argument('role', help='Role of the switch (leaf, spine, etc.)')
    parser.add_argument('switch_name', help='Name of the switch')
    
    args = parser.parse_args()
    
    try:
        # Create InterfaceManager instance
        interface_manager = InterfaceManager()
        
        # Update switch interfaces
        success = interface_manager.update_switch_interfaces(
            args.fabric_name, 
            args.role, 
            args.switch_name
        )
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
