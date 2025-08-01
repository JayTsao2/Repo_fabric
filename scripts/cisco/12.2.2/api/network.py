import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3
urllib3.disable_warnings(InsecureRequestWarning)
from .utils import *
import json
from typing import Dict, Any, List

def get_networks(fabric, network_dir="networks", network_template_config_dir="networks/network_templates", network_filter="", range=0):
    # range = show the networks from 0 to {range}
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks")
    headers = get_api_key_header()
    headers["range"] = f"0-{range}"
    query_params = {}
    if network_filter != "":
        query_params["filter"] = network_filter
    r = requests.get(url, headers=headers, params=query_params, verify=False)
    check_status_code(r)

    networks = r.json()
    # if the directory does not exist, create it
    if not os.path.exists(network_dir):
        os.makedirs(network_dir)
    if not os.path.exists(network_template_config_dir):
        os.makedirs(network_template_config_dir)
    
    # Save networks to a file, networks is an array of network objects
    for network in networks:
        network_id = network.get("networkId", "unknown")
        network_name = network.get("networkName", "unknown")
        network_template_config = network.get("networkTemplateConfig", {})
        filename = f"{network_dir}/{fabric}_{network_id}_{network_name}.json"
        with open(filename, "w") as f:
            json.dump(network, f, indent=4)
            print(f"Network config for {network_name} (ID: {network_id}) is saved to {filename}")
        if network_template_config:
            network_template_config = json.loads(network_template_config) if isinstance(network_template_config, str) else network_template_config
            network_template_config_filename = f"{network_template_config_dir}/{fabric}_{network_id}_{network_name}.json"
            with open(network_template_config_filename, "w") as f:
                json.dump(network_template_config, f, indent=4)
                print(f"Network config template for {network_name} (ID: {network_id}) is saved to {network_template_config_filename}")

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

def get_network_attachment(fabric, network_dir="networks", networkname=""):
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks/{networkname}/attachments")
    headers = get_api_key_header()
    r = requests.get(url, headers=headers, verify=False)
    check_status_code(r)

    if not os.path.exists(network_dir):
        os.makedirs(network_dir)
    if not os.path.exists(f"{network_dir}/attachments"):
        os.makedirs(f"{network_dir}/attachments")
    attachments = r.json()
    for attachment in attachments:
        attachment_switch_name = attachment.get("switchName", "unknown")
        filename = f"{network_dir}/attachments/{fabric}_{networkname}_{attachment_switch_name}.json"
        with open(filename, "w") as f:
            json.dump(attachment, f, indent=4)
            print(f"Network attachments for {networkname} on switch {attachment_switch_name} are saved to {filename}")

def attach_network(fabric_name: str, network_name: str, serial_number: str, switch_ports: str, vlan: int) -> bool:
    """
    Attach a network to switch interfaces using payload data.
    
    Args:
        fabric_name: Name of the fabric
        network_name: Name of the network
        serial_number: Serial number of the switch
        switch_ports: Comma-separated list of switch ports
        vlan: VLAN ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    payload = {
        "fabric": fabric_name,
        "networkName": network_name,
        "serialNumber": serial_number,
        "switchPorts": switch_ports,
        "vlan": vlan,
        "deployment": True,
        "instanceValues": "",
        "freeformConfig": ""
    }
    
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/networks/{network_name}/attachments")
    r = requests.post(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name=f"Attach {network_name} to port {switch_ports}")

def detach_network(fabric_name: str, network_name: str, serial_number: str, detach_switch_ports: str, vlan: int) -> bool:
    """
    Detach a network from switch interfaces using payload data.
    
    Args:
        fabric_name: Name of the fabric
        network_name: Name of the network
        serial_number: Serial number of the switch
        detach_switch_ports: Comma-separated list of switch ports to detach
        vlan: VLAN ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    payload = {
        "fabric": fabric_name,
        "networkName": network_name,
        "serialNumber": serial_number,
        "detachSwitchPorts": detach_switch_ports,
        "vlan": vlan,
        "deployment": False,
        "instanceValues": "",
        "freeformConfig": ""
    }
    
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/networks/{network_name}/attachments")
    r = requests.post(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name=f"Detach {network_name} from port {detach_switch_ports}")

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