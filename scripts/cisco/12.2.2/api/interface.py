import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3
urllib3.disable_warnings(InsecureRequestWarning)
from .utils import *
import json
import os
from typing import Dict, Any, List

def update_interface(fabric_name: str, policy: str, interfaces_payload: List[Dict[str, Any]]) -> bool:
    """
    Update interface configuration using NDFC API.
    
    Args:
        fabric_name: Name of the fabric
        policy: Interface policy type (e.g., "int_access_host", "int_trunk_host", "int_routed_host")
        interfaces_payload: List of interface configurations
    
    Returns:
        Boolean indicating success
    """
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface")
    headers = get_api_key_header()
    
    payload = {
        "policy": policy,
        "interfaces": interfaces_payload
    }
    
    r = requests.put(url, headers=headers, json=payload, verify=False)
    check_status_code(r, operation_name="Update Interfaces")

def get_interfaces(serial_number: str = None, if_name: str = None, template_name: str = None, 
                  interface_dir: str = "interfaces", save_by_policy: bool = True) -> List[Dict[str, Any]]:
    """
    Get interfaces from NDFC API with optional filtering.
    
    Args:
        serial_number: Filter by device serial number
        if_name: Filter by specific interface name (e.g., "Ethernet1/1")
        template_name: Filter by policy template (e.g., "int_trunk_host", "int_access_host", "int_routed_host")
        interface_dir: Directory to save interface data
        save_by_policy: Whether to save interfaces grouped by policy type
    
    Returns:
        List of interface data from the API
    """
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface")
    headers = get_api_key_header()
    
    # Build query parameters
    query_params = {}
    if serial_number:
        query_params["serialNumber"] = serial_number
    if if_name:
        query_params["ifName"] = if_name
    if template_name:
        query_params["templateName"] = template_name
    
    try:
        r = requests.get(url, headers=headers, params=query_params, verify=False)
        check_status_code(r)
        
        interfaces_data = r.json()
        
        # Create directory if it doesn't exist
        if not os.path.exists(interface_dir):
            os.makedirs(interface_dir)
        
        if save_by_policy:
            _save_interfaces_by_policy(interfaces_data, interface_dir, serial_number)
        else:
            _save_all_interfaces(interfaces_data, interface_dir, serial_number)
        
        return interfaces_data
        
    except Exception as e:
        print(f"❌ Error getting interfaces: {e}")
        return []

def _save_interfaces_by_policy(interfaces_data: List[Dict], interface_dir: str, serial_number: str = None):
    """Save interfaces grouped by policy type."""
    policy_groups = {
        "int_access_host": [],
        "int_trunk_host": [], 
        "int_routed_host": [],
        "other": []
    }
    
    for policy_group in interfaces_data:
        policy = policy_group.get("policy", "unknown")
        interfaces = policy_group.get("interfaces", [])
        
        if policy in policy_groups:
            policy_groups[policy].extend(interfaces)
        else:
            policy_groups["other"].extend(interfaces)
    
    # Save each policy group to separate files
    for policy, interfaces in policy_groups.items():
        if interfaces:
            filename_suffix = f"_{serial_number}" if serial_number else ""
            filename = f"{policy}_interfaces{filename_suffix}.json"
            filepath = os.path.join(interface_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(interfaces, f, indent=2, ensure_ascii=False)

def _save_all_interfaces(interfaces_data: List[Dict], interface_dir: str, serial_number: str = None):
    """Save all interfaces in a single file."""
    filename_suffix = f"_{serial_number}" if serial_number else ""
    filename = f"all_interfaces{filename_suffix}.json"
    filepath = os.path.join(interface_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(interfaces_data, f, indent=2, ensure_ascii=False)

def update_admin_status(payload: List[Dict[str, Any]]) -> bool:
    """
    Update interface admin status (enable/disable) for interfaces without policies.
    
    Args:
        interfaces: List of interfaces with admin status configuration
        
    Returns:
        True if successful, False otherwise
    """
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface/adminstatus")
    headers = get_api_key_header()
    
    r = requests.post(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name="Update Admin Status")
