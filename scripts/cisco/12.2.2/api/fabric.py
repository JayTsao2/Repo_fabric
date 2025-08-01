import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3
urllib3.disable_warnings(InsecureRequestWarning)
from .utils import *
import json
from typing import Dict, Any, Optional

def get_fabrics():
    """Get all fabrics from NDFC."""
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics")
    headers = get_api_key_header()

    r = requests.get(url=url, headers=headers, verify=False)
    success = check_status_code(r)
    
    if success:
        fabrics = r.json()
        with open("fabrics.json", "w") as f:
            json.dump(fabrics, f, indent=4)
        return fabrics
    else:
        return None

def get_fabric(fabric_name: str, fabric_dir: str = "fabrics") -> Optional[Dict[str, Any]]:
    """Get specific fabric configuration from NDFC."""
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric_name}")
    
    headers = get_api_key_header()

    r = requests.get(url=url, headers=headers, verify=False)
    success = check_status_code(r)
    
    if not success:
        return None
    
    try: 
        data = r.json()
        if not os.path.exists(fabric_dir):
            os.makedirs(fabric_dir)
        filename = f"{fabric_dir}/{fabric_name}.json"
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
            print(f"Fabric {fabric_name} data is saved to {filename}")
        return data
    except Exception as e:
        print(f"Error: {e}")
        return None

def delete_fabric(fabric_name: str) -> bool:
    """Delete a fabric from NDFC."""
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric_name}")

    headers = get_api_key_header()
    r = requests.delete(url=url, headers=headers, verify=False)

    return check_status_code(r, operation_name="Delete Fabric")

def create_fabric(fabric_name: str, template_name: str, payload_data: Dict[str, Any]) -> bool:
    """
    Create a fabric using provided payload data.
    
    Args:
        fabric_name: Name of the fabric to create
        template_name: Template type (Easy_Fabric, External_Fabric, MSD_Fabric, etc.)
        payload_data: Complete nvPairs payload data
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Clean payload by removing invalid fields
    invalid_fields = ["USE_LINK_LOCAL", "ISIS_OVERLOAD_ENABLE", "ISIS_P2P_ENABLE", 
                    "PNP_ENABLE_INTERNAL", "DOMAIN_NAME_INTERNAL"]
    cleaned_payload = {k: v for k, v in payload_data.items() if k not in invalid_fields}
    
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric_name}/{template_name}")
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    r = requests.post(url, headers=headers, data=json.dumps(cleaned_payload), verify=False)

    return check_status_code(r, operation_name="Create Fabric")

def update_fabric(fabric_name: str, template_name: str, payload_data: Dict[str, Any]) -> bool:
    """
    Update a fabric using provided payload data.
    
    Args:
        fabric_name: Name of the fabric to update
        template_name: Template type (Easy_Fabric, External_Fabric, MSD_Fabric, etc.)
        payload_data: Complete nvPairs payload data
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Clean payload by removing invalid fields
    invalid_fields = ["USE_LINK_LOCAL", "ISIS_OVERLOAD_ENABLE", "ISIS_P2P_ENABLE", 
                        "PNP_ENABLE_INTERNAL", "DOMAIN_NAME_INTERNAL"]
    cleaned_payload = {k: v for k, v in payload_data.items() if k not in invalid_fields}
    
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric_name}/{template_name}")
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    r = requests.put(url, headers=headers, data=json.dumps(cleaned_payload), verify=False)

    return check_status_code(r, operation_name="Update Fabric")

def recalculate_config(fabric_name: str) -> bool:
    """Recalculate fabric configuration."""
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric_name}/config-save")
    headers = get_api_key_header()
    r = requests.post(url, headers=headers, verify=False)

    return check_status_code(r, operation_name="Recalculate Config")

def deploy_fabric_config(fabric_name: str) -> bool:
    """Deploy fabric configuration."""
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric_name}/config-deploy")
    headers = get_api_key_header()
    r = requests.post(url, headers=headers, verify=False)

    return check_status_code(r, operation_name="Deploy Fabric Config")

def get_pending_config(fabric_name: str) -> Optional[Dict[str, Any]]:
    """Get pending configuration for a fabric and save in formatted text file."""
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric_name}/config-preview")
    headers = get_api_key_header()
    
    r = requests.get(url=url, headers=headers, verify=False)
    
    if not check_status_code(r):
        return None
    
    try:
        data = r.json()
        
        txt_filename = "pending.txt"
        with open(txt_filename, "w") as f:
            for switch_data in data:
                switch_name = switch_data.get("switchName", "Unknown")
                pending_config = switch_data.get("pendingConfig", [])
                
                f.write(f"- {switch_name}\n")
                for command in pending_config:
                    f.write(f"{command}\n")
                f.write("===\n")
        
        print(f"Formatted pending configuration for fabric {fabric_name} saved to {txt_filename}")
        return data
        
    except Exception as e:
        print(f"Error getting pending config for fabric {fabric_name}: {e}")
        return None

def add_MSD(parent_fabric_name: str, child_fabric_name: str) -> bool:
    """Add a child fabric to a Multi-Site Domain."""
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/msdAdd")
    headers = get_api_key_header()
    payload = {
        "destFabric": parent_fabric_name,
        "sourceFabric": child_fabric_name
    }
    r = requests.post(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name="Add MSD")

def remove_MSD(parent_fabric_name: str, child_fabric_name: str) -> bool:
    """Remove a child fabric from a Multi-Site Domain."""
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/msdExit")
    headers = get_api_key_header()
    payload = {
        "destFabric": parent_fabric_name,
        "sourceFabric": child_fabric_name
    }
    r = requests.post(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name="Remove MSD")
