import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3
urllib3.disable_warnings(InsecureRequestWarning)
from .utils import *
import json
import os
from typing import Dict, Any, List

def get_networks(fabric):
    # range = show the networks from 0 to {range}
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks")
    headers = get_api_key_header()
    headers["range"] = f"0-9999"
    r = requests.get(url, headers=headers, verify=False)
    check_status_code(r, f"Get Networks for fabric {fabric}")
    return r.json()

def get_network(fabric, network_name, network_dir="networks", network_template_config_dir="networks/network_templates"):
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks/{network_name}")
    headers = get_api_key_header()
    r = requests.get(url, headers=headers, verify=False)
    check_status_code(r)

    network = r.json()
    # Save the network to a file
    network_id = network.get("networkId", "unknown")
    filename = f"{network_dir}/{fabric}_{network_id}_{network_name}.json"
    with open(filename, "w") as f:
        json.dump(network, f, indent=4)
        print(f"Network config for {network_name} (ID: {network_id}) is saved to {filename}")

    # Save the network template config if it exists
    network_template_config = network.get("networkTemplateConfig", {})
    if network_template_config:
        network_template_config_filename = f"{network_template_config_dir}/{fabric}_{network_id}_{network_name}.json"
        network_template_config = json.loads(network_template_config) if isinstance(network_template_config, str) else network_template_config
        with open(network_template_config_filename, "w") as f:
            json.dump(network_template_config, f, indent=4)
            print(f"Network config template for {network_name} (ID: {network_id}) is saved to {network_template_config_filename}")

def create_network(fabric_name: str, network_payload: Dict[str, Any], template_payload: Dict[str, Any]) -> bool:
    """
    Create a network using direct payload data.
    
    Args:
        fabric_name: Name of the fabric
        network_payload: Main network configuration payload
        template_payload: Network template configuration payload
        
    Returns:
        bool: True if successful, False otherwise
    """
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    # Convert template payload to JSON string if provided
    template_config_str = json.dumps(template_payload) if template_payload else ""
    
    # Create the final payload
    payload = network_payload.copy()
    payload["networkTemplateConfig"] = template_config_str
    
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/networks")
    r = requests.post(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name="Create Network")

def update_network(fabric_name: str, network_payload: Dict[str, Any], template_payload: Dict[str, Any]) -> bool:
    """
    Update a network using direct payload data.
    
    Args:
        fabric_name: Name of the fabric
        network_payload: Main network configuration payload
        template_payload: Network template configuration payload
        
    Returns:
        bool: True if successful, False otherwise
    """
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    # Convert template payload to JSON string if provided
    template_config_str = json.dumps(template_payload) if template_payload else ""
    
    # Create the final payload
    payload = network_payload.copy()
    payload["networkTemplateConfig"] = template_config_str
    
    network_name = network_payload.get('networkName')
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/networks/{network_name}")
    r = requests.put(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name="Update Network")

def delete_network(fabric_name: str, network_name: str) -> bool:
    """
    Delete a network.
    
    Args:
        fabric_name: Name of the fabric
        network_name: Name of the network to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    headers = get_api_key_header()
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/networks/{network_name}")
    r = requests.delete(url, headers=headers, verify=False)
    return check_status_code(r, operation_name="Delete Network")

def get_network_attachment(fabric, network_dir="networks", networkname="", save_files=True):
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks/{networkname}/attachments")
    headers = get_api_key_header()
    r = requests.get(url, headers=headers, verify=False)
    check_status_code(r, f"Get Network Attachments for {networkname} in fabric {fabric}")

    attachments = r.json()
    
    # Only save files if requested
    if save_files:
        if not os.path.exists(network_dir):
            os.makedirs(network_dir)
        if not os.path.exists(f"{network_dir}/attachments"):
            os.makedirs(f"{network_dir}/attachments")
        
        for attachment in attachments:
            attachment_switch_name = attachment.get("switchName", "unknown")
            filename = f"{network_dir}/attachments/{fabric}_{networkname}_{attachment_switch_name}.json"
            with open(filename, "w") as f:
                json.dump(attachment, f, indent=4)
                print(f"Network attachments for {networkname} on switch {attachment_switch_name} are saved to {filename}")
    
    # Return the attachments data for programmatic use
    return attachments

def attach_network(payload: List[Dict[str, Any]]) -> bool:
    """
    Attach networks to devices using the new payload format.
    
    Args:
        payload: List of network attachment configurations
        
    Returns:
        bool: True if successful, False otherwise
    """
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/networks/multiattach")
    r = requests.post(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name=f"Attach networks")

def detach_network(fabric_name: str, payload: List[Dict[str, Any]]) -> bool:
    """
    Detach networks from devices using the new payload format.
    
    Args:
        fabric_name: Name of the fabric
        payload: List of network detachment configurations
        
    Returns:
        bool: True if successful, False otherwise
    """
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/networks/attachments")
    r = requests.post(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name=f"Detach networks")

def preview_networks(fabric, network_names):
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    # Preview networks
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks/preview")
    query_params = {
        "network-names": network_names
    }
    
    r = requests.get(url, headers=headers, params=query_params, verify=False)
    return check_status_code(r, operation_name="Preview Networks")

def deploy_networks(fabric, network_names):
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    # Deploy networks
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks/deployments")
    payload = {
        "networkNames": network_names
    }
    
    r = requests.post(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name="Deploy Networks")