#!/usr/bin/env python3
"""
Switch Management Module - Core Components

Provides YAML-based switch management for Cisco NDFC:
- Switch discovery using switch YAML files
- Automatic payload generation from YAML configuration
- Integration with NDFC switch discovery API
"""

import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import paramiko
import time

# Setup import paths
sys.path.append(str(Path(__file__).parent.parent.absolute()))
import api.switch as switch_api
from modules.config_utils import load_yaml_file

# Valid switch roles enum
VALID_SWITCH_ROLES = {
    "leaf",
    "spine", 
    "super spine",
    "border gateway",
    "border gateway spine",
    "border gateway super spine",
    "core router",
    "edge router",
    "tor"
}

@dataclass
class SwitchConfig:
    """Switch configuration data structure."""
    fabric_name: str
    sys_name: str
    serial_number: str
    ip_address: str
    platform: str
    version: str
    device_index: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls."""
        return {
            "sysName": self.sys_name,
            "serialNumber": self.serial_number,
            "ipaddr": self.ip_address,
            "platform": self.platform,
            "deviceIndex": self.device_index,
            "version": self.version
        }

class SwitchManager:
    """Unified switch operations manager with YAML configuration support."""
    
    def __init__(self):
        """Initialize with configuration paths."""
        self.repo_root = Path(__file__).resolve().parents[5]  # Go up 5 levels to reach Repo_fabric
        self.config_base_path = self.repo_root / "network_configs" / "3_node"
    
    def _validate_switch_role(self, role: str) -> bool:
        """Validate if the role is in the allowed enum values."""
        role_lower = role.lower().strip()
        if role_lower not in VALID_SWITCH_ROLES:
            print(f"Error: Invalid switch role '{role}'. Valid roles are:")
            for valid_role in sorted(VALID_SWITCH_ROLES):
                print(f"  - {valid_role}")
            return False
        return True
    
    def _get_switch_config_path(self, fabric_name: str, role: str, switch_name: str) -> Path:
        """Get switch configuration file path."""
        return self.config_base_path / fabric_name / role / f"{switch_name}.yaml"
    
    def _load_switch_config(self, fabric_name: str, role: str, switch_name: str) -> Optional[Dict[str, Any]]:
        """Load switch configuration from YAML file."""
        config_path = self._get_switch_config_path(fabric_name, role, switch_name)
        
        if not config_path.exists():
            print(f"Switch configuration not found: {config_path}")
            return None
        
        print(f"Loading config: {config_path.name}")
        return load_yaml_file(str(config_path))
    
    def _find_switch_config(self, switch_name: str) -> Optional[tuple[str, str, Dict[str, Any]]]:
        """Find switch configuration by name across all fabrics and roles."""
        # Search through all fabric directories in 3_node
        for fabric_dir in self.config_base_path.iterdir():
            if not fabric_dir.is_dir():
                continue
            
            # Search through all role directories (leaf, spine, border_gateway, etc.)
            for role_dir in fabric_dir.iterdir():
                if not role_dir.is_dir():
                    continue
                
                # Look for the switch YAML file
                switch_file = role_dir / f"{switch_name}.yaml"
                if switch_file.exists():
                    config_data = load_yaml_file(str(switch_file))
                    if config_data:
                        return fabric_dir.name, role_dir.name, config_data
        
        return None
    
    def _extract_model_name(self, platform: str) -> str:
        """Extract model name from platform string."""
        # Extract model from platform (e.g., "N9K-C9300v" -> "N9K")
        if "-" in platform:
            return platform.split("-")[0]
        return platform
    
    def _build_switch_config(self, fabric_name: str, role: str, switch_name: str, 
                           switch_data: Dict[str, Any]) -> SwitchConfig:
        """Build SwitchConfig from YAML data."""
        ip_address = switch_data.get("IP Address", "")
        serial_number = switch_data.get("Serial Number", "")
        platform = switch_data.get("Platform", "")
        version = switch_data.get("Version", "9.3(15)")  # Default version if not specified
        
        # Extract model name for device index
        model_name = self._extract_model_name(platform)
        device_index = f"{switch_name}-{model_name}({serial_number})"
        
        return SwitchConfig(
            fabric_name=fabric_name,
            sys_name=switch_name,
            serial_number=serial_number,
            ip_address=ip_address,
            platform=platform,
            version=version,
            device_index=device_index
        )
    
    def _build_discovery_payload(self, switch_config: SwitchConfig, preserve_config: bool = False) -> Dict[str, Any]:
        """Build discovery payload for API."""
        return {
            "seedIP": switch_config.ip_address,
            "username": "admin",
            "password": "",  # Will be filled from environment
            "maxHops": 0,
            "preserveConfig": preserve_config,
            "switches": [switch_config.to_dict()],
            "platform": "null"
        }
    
    def discover_switch(self, fabric_name: str, role: str, switch_name: str, preserve_config: bool = False) -> bool:
        """Discover switch based on YAML configuration."""
        try:
            # Load switch configuration
            switch_data = self._load_switch_config(fabric_name, role, switch_name)
            if not switch_data:
                return False
            
            # Build switch configuration
            switch_config = self._build_switch_config(fabric_name, role, switch_name, switch_data)
            
            # Generate discovery payload
            payload = self._build_discovery_payload(switch_config, preserve_config)
            
            print(f"Discovering switch: {switch_name} ({switch_config.serial_number})")
            
            # Call API to discover switch
            success = switch_api.discover_switch_from_payload(fabric_name, payload)
            
            if success:
                print(f"Successfully discovered switch {switch_name}")
            
            return success
            
        except Exception as e:
            print(f"Error discovering switch: {e}")
            return False
    
    def delete_switch(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Delete switch based on YAML configuration."""
        try:
            # Load switch configuration to get serial number
            switch_data = self._load_switch_config(fabric_name, role, switch_name)
            if not switch_data:
                return False
            
            serial_number = switch_data.get("Serial Number")
            if not serial_number:
                print(f"Error: Serial Number not found in {switch_name} configuration")
                return False
            
            print(f"Deleting switch: {switch_name} ({serial_number})")
            
            # Call API to delete switch
            switch_api.delete_switch(fabric_name, serial_number)
            print(f"Successfully deleted switch {switch_name}")
            return True
            
        except Exception as e:
            print(f"Error deleting switch: {e}")
            return False
    
    def set_switch_role(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Set switch role based on YAML configuration."""
        try:
            # Load switch configuration to get serial number and role
            switch_data = self._load_switch_config(fabric_name, role, switch_name)
            if not switch_data:
                return False
            
            serial_number = switch_data.get("Serial Number")
            if not serial_number:
                print(f"Error: Serial Number not found in {switch_name} configuration")
                return False
            
            switch_role = switch_data.get("Role")
            if not switch_role:
                print(f"Error: Role not found in {switch_name} configuration")
                return False
            
            # Validate the switch role
            if not self._validate_switch_role(switch_role):
                return False
            
            # Convert role to lowercase for API
            switch_role_lower = switch_role.lower().strip()
            
            print(f"Setting role for switch: {switch_name} ({serial_number}) to '{switch_role_lower}'")
            
            # Call API to set switch role
            switch_api.set_switch_role(serial_number, switch_role_lower)
            print(f"Successfully set role for switch {switch_name}")
            return True
            
        except Exception as e:
            print(f"Error setting switch role: {e}")
            return False
    
    def set_switch_role_by_name(self, switch_name: str) -> bool:
        """Set switch role by searching for switch name across all configurations."""
        try:
            # Find switch configuration across all fabrics and roles
            result = self._find_switch_config(switch_name)
            if not result:
                print(f"Switch configuration not found for: {switch_name}")
                return False
            
            fabric_name, role_dir, switch_data = result
            
            serial_number = switch_data.get("Serial Number")
            if not serial_number:
                print(f"Error: Serial Number not found in {switch_name} configuration")
                return False
            
            switch_role = switch_data.get("Role")
            if not switch_role:
                print(f"Error: Role not found in {switch_name} configuration")
                return False
            
            # Validate the switch role
            if not self._validate_switch_role(switch_role):
                return False
            
            # Convert role to lowercase for API
            switch_role_lower = switch_role.lower().strip()
            
            print(f"Found switch: {switch_name} in fabric {fabric_name}/{role_dir}")
            print(f"Setting role for switch: {switch_name} ({serial_number}) to '{switch_role_lower}'")
            
            # Call API to set switch role
            switch_api.set_switch_role(serial_number, switch_role_lower)
            print(f"Successfully set role for switch {switch_name}")
            return True
            
        except Exception as e:
            print(f"Error setting switch role: {e}")
            return False
    
    def change_switch_ip(self, fabric_name: str, role: str, switch_name: str, 
                        original_ip: str, new_ip: str) -> bool:
        """Change switch management IP through SSH and update NDFC."""
        try:
            # Load switch configuration
            switch_data = self._load_switch_config(fabric_name, role, switch_name)
            if not switch_data:
                return False
            
            serial_number = switch_data.get("Serial Number")
            if not serial_number:
                print(f"Error: Serial Number not found in {switch_name} configuration")
                return False
            
            # Parse IP addresses
            original_ip_only = original_ip.split('/')[0]
            new_ip_with_mask = new_ip
            new_ip_only = new_ip.split('/')[0]
            
            print(f"Changing IP for switch: {switch_name} ({serial_number})")
            print(f"From: {original_ip} To: {new_ip}")
            
            # Step 1: SSH to switch and change management IP
            print("Step 1: Connecting to switch via SSH")
            if not self._ssh_change_management_ip(original_ip_only, new_ip_with_mask):
                return False
            
            # Step 2: Update discovery IP in NDFC
            print("Step 2: Updating discovery IP in NDFC")
            switch_api.change_discovery_ip(fabric_name, serial_number, new_ip_only)
            
            # Step 3: Rediscover device
            print("Step 3: Rediscovering device")
            switch_api.rediscover_device(fabric_name, serial_number)
            
            print(f"Successfully changed IP for switch {switch_name}")
            return True
            
        except Exception as e:
            print(f"Error changing switch IP: {e}")
            return False
    
    def _ssh_change_management_ip(self, original_ip: str, new_ip_with_mask: str) -> bool:
        """SSH to switch and change management IP address."""
        try:
            # Load environment for password from the correct path
            from dotenv import load_dotenv
            # Go to the script directory and then to api/.env
            script_dir = Path(__file__).resolve().parents[2]  # Go up to scripts/cisco/12.2.2/
            env_path = script_dir / "api" / ".env"
            load_dotenv(env_path)
            password = os.getenv("SWITCH_PASSWORD")
            
            if not password:
                print("Error: SWITCH_PASSWORD not found in environment")
                print(f"Please check .env file at: {env_path}")
                return False
            
            # SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            print(f"Connecting to {original_ip}")
            ssh.connect(original_ip, username="admin", password=password, timeout=30)
            
            # Execute IP change command
            command = f"configure terminal ; interface mgmt0 ; ip address {new_ip_with_mask} ; exit ; exit"
            print(f"Executing: ip address {new_ip_with_mask}")
            
            stdin, stdout, stderr = ssh.exec_command(command)
            
            # Wait for command execution
            time.sleep(2)
            
            ssh.close()
            print("IP address changed successfully")
            return True
            
        except Exception as e:
            print(f"SSH Error: {e}")
            return False
    
    def set_switch_freeform(self, fabric_name: str, role: str, switch_name: str) -> bool:
        """Apply freeform configuration to switch based on YAML configuration."""
        try:
            # Load switch configuration
            switch_data = self._load_switch_config(fabric_name, role, switch_name)
            if not switch_data:
                return False
            
            serial_number = switch_data.get("Serial Number")
            if not serial_number:
                print(f"Error: Serial Number not found in {switch_name} configuration")
                return False
            
            freeform_config_path = switch_data.get("Switch Freeform Config")
            if not freeform_config_path:
                print(f"Error: Switch Freeform Config not found in {switch_name} configuration")
                return False
            
            print(f"Applying freeform config for switch: {switch_name} ({serial_number})")
            print(f"Freeform config file: {freeform_config_path}")
            
            # Parse freeform configuration file
            cli_commands = self._parse_freeform_config(fabric_name, role, freeform_config_path)
            if not cli_commands:
                return False
            
            print(f"Parsed {len(cli_commands.splitlines())} command lines")
            print("Executing freeform configuration via NDFC API")
            
            # Call API to execute freeform configuration
            switch_api.exec_freeform_config(serial_number, cli_commands)
            print(f"Successfully applied freeform config for switch {switch_name}")
            return True
            
        except Exception as e:
            print(f"Error applying freeform config: {e}")
            return False
    
    def _parse_freeform_config(self, fabric_name: str, role: str, freeform_config_path: str) -> Optional[str]:
        """Parse freeform configuration file and return CLI commands."""
        try:
            # Build the full path to the freeform config file
            # The path is relative to the switch YAML file location
            switch_dir = self.config_base_path / fabric_name / role
            config_file_path = switch_dir / freeform_config_path
            
            if not config_file_path.exists():
                print(f"Freeform config file not found: {config_file_path}")
                return None
            
            print(f"Reading freeform config: {config_file_path.name}")
            
            # Read the configuration file
            with open(config_file_path, 'r', encoding='utf-8') as f:
                cli_commands = f.read().strip()
            
            if not cli_commands:
                print("Warning: Freeform config file is empty")
                return None
            
            return cli_commands
            
        except Exception as e:
            print(f"Error parsing freeform config: {e}")
            return None

# --- Expose the SwitchManager class ---
__all__ = ['SwitchManager', 'SwitchConfig']
