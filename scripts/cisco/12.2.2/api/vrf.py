import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3
urllib3.disable_warnings(InsecureRequestWarning)
from .utils import *
import json
from typing import Dict, Any, List

def get_VRFs(fabric, vrf_dir="vrfs", vrf_template_config_dir="vrf_template_config_dirs", vrf_filter="", range=0):
    # range = show the vrfs from 0 to {range}
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/vrfs")
    headers = get_api_key_header()
    headers["range"] = f"0-{range}"
    query_params = {}
    if vrf_filter != "":
        query_params["filter"] = vrf_filter
    r = requests.get(url, headers=headers, params=query_params, verify=False)
    check_status_code(r)

    vrfs = r.json()
    # if the directory does not exist, create it
    if not os.path.exists(vrf_dir):
        os.makedirs(vrf_dir)
    if not os.path.exists(vrf_template_config_dir):
        os.makedirs(vrf_template_config_dir)
    # Save vrfs to a file, vrfs is a array of vrf objects
    for vrf in vrfs:
        vrf_id = vrf.get("vrfId", "unknown")
        vrf_name = vrf.get("vrfName", "unknown")
        vrf_template_config = vrf.get("vrfTemplateConfig", {})
        filename = f"{vrf_dir}/{fabric}_{vrf_id}_{vrf_name}.json"
        with open(filename, "w") as f:
            json.dump(vrf, f, indent=4)
            print(f"VRF config for {vrf_name} (ID: {vrf_id}) is saved to {filename}")
        if vrf_template_config:
            vrf_template_config = json.loads(vrf_template_config) if isinstance(vrf_template_config, str) else vrf_template_config
            vrf_template_config_filename = f"{vrf_template_config_dir}/{fabric}_{vrf_id}_{vrf_name}.json"
            with open(vrf_template_config_filename, "w") as f:
                json.dump(vrf_template_config, f, indent=4)
                print(f"VRF config template for {vrf_name} (ID: {vrf_id}) is saved to {vrf_template_config_filename}")

def create_vrf(fabric_name: str, vrf_payload: Dict[str, Any], template_payload: Dict[str, Any]) -> bool:
    """
    Create a VRF using direct payload data.
    
    Args:
        fabric_name: Name of the fabric
        vrf_payload: Main VRF configuration payload
        template_payload: VRF template configuration payload
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        headers = get_api_key_header()
        headers['Content-Type'] = 'application/json'
        
        # Convert template payload to JSON string
        vrf_payload["vrfTemplateConfig"] = json.dumps(template_payload)
        
        url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs")
        
        r = requests.post(url, headers=headers, json=vrf_payload, verify=False)
        check_status_code(r)
        
        return True
        
    except Exception as e:
        print(f"Error creating VRF {vrf_payload.get('vrfName', 'unknown')}: {e}")
        return False

def update_vrf(fabric_name: str, vrf_name: str, vrf_payload: Dict[str, Any], template_payload: Dict[str, Any]) -> bool:
    """
    Update a VRF using direct payload data.
    
    Args:
        fabric_name: Name of the fabric
        vrf_name: Name of the VRF to update
        vrf_payload: Main VRF configuration payload
        template_payload: VRF template configuration payload
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        headers = get_api_key_header()
        headers['Content-Type'] = 'application/json'
        
        # Convert template payload to JSON string
        vrf_payload["vrfTemplateConfig"] = json.dumps(template_payload)
        
        url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/{vrf_name}")
        
        r = requests.put(url, headers=headers, json=vrf_payload, verify=False)
        check_status_code(r)
        
        return True
        
    except Exception as e:
        print(f"Error updating VRF {vrf_name}: {e}")
        return False

def delete_vrf(fabric_name: str, vrf_name: str) -> bool:
    """
    Delete a VRF from a fabric.
    
    Args:
        fabric_name: Name of the fabric
        vrf_name: Name of the VRF to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/{vrf_name}")
        headers = get_api_key_header()
        
        r = requests.delete(url, headers=headers, verify=False)
        check_status_code(r)
        
        return True
        
    except Exception as e:
        print(f"Error deleting VRF {vrf_name}: {e}")
        return False

def update_vrf_attachment(fabric_name: str, attachment_payload: Dict[str, Any]) -> bool:
    """
    Update VRF attachment using direct payload data.
    
    Args:
        fabric_name: Name of the fabric
        attachment_payload: VRF attachment configuration payload
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        headers = get_api_key_header()
        headers['Content-Type'] = 'application/json'
        
        print(f"Updating VRF attachment in fabric {fabric_name}...")
        url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/attachments")
        
        r = requests.post(url, headers=headers, json=attachment_payload, verify=False)
        check_status_code(r)
        
        return True
        
    except Exception as e:
        print(f"Error updating VRF attachment: {e}")
        return False

def attach_vrf_to_switches(fabric_name: str, vrf_name: str, attachment_payload: List[Dict[str, Any]]) -> bool:
    """
    Attach VRF to switches by setting deployment=true in the attachment configuration.
    
    Args:
        fabric_name: Name of the fabric
        vrf_name: Name of the VRF to attach
        attachment_payload: VRF attachment configuration payload (array format)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        headers = get_api_key_header()
        headers['Content-Type'] = 'application/json'
        
        # Ensure deployment is set to true for attachment
        for vrf_attachment in attachment_payload:
            if "lanAttachList" in vrf_attachment:
                for attach_item in vrf_attachment["lanAttachList"]:
                    attach_item["deployment"] = True
        
        print(f"Attaching VRF {vrf_name} to switches in fabric {fabric_name}...")
        
        url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/attachments")
        
        r = requests.post(url, headers=headers, json=attachment_payload, verify=False)
        check_status_code(r)
        
        print(f"✅ VRF {vrf_name} successfully attached to switches")
        return True
        
    except Exception as e:
        print(f"❌ Error attaching VRF {vrf_name} to switches: {e}")
        return False

def detach_vrf_from_switches(fabric_name: str, vrf_name: str, attachment_payload: List[Dict[str, Any]]) -> bool:
    """
    Detach VRF from switches by setting deployment=false in the attachment configuration.
    
    Args:
        fabric_name: Name of the fabric
        vrf_name: Name of the VRF to detach
        attachment_payload: VRF attachment configuration payload (array format)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        headers = get_api_key_header()
        headers['Content-Type'] = 'application/json'
        
        # Ensure deployment is set to false for detachment
        for vrf_attachment in attachment_payload:
            if "lanAttachList" in vrf_attachment:
                for attach_item in vrf_attachment["lanAttachList"]:
                    attach_item["deployment"] = False
        
        print(f"Detaching VRF {vrf_name} from switches in fabric {fabric_name}...")
        
        url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs/attachments")
        
        r = requests.post(url, headers=headers, json=attachment_payload, verify=False)
        check_status_code(r)
        
        print(f"✅ VRF {vrf_name} successfully detached from switches")
        return True
        
    except Exception as e:
        print(f"❌ Error detaching VRF {vrf_name} from switches: {e}")
        return False

# Legacy functions for backward compatibility

if __name__ == "__main__":
    # get_VRFs(fabric="Site1-Greenfield", vrf_dir="vrfs", vrf_template_config_dir="vrfs/vrf_templates", vrf_filter="vrfId==50000", range=0)
    # get_VRFs(fabric="Site1-TSMC", vrf_dir="vrfs", vrf_template_config_dir="vrfs/vrf_templates", vrf_filter="", range=0)
    # create_VRF(filename="vrfs/Site1-TSMC_50000_bluevrf.json", vrf_template_config_file="vrfs/vrf_templates/Site1-TSMC_50000_bluevrf.json")
    # update_VRF(filename="vrfs/Site1-TSMC_50000_bluevrf.json", vrf_template_config_file="vrfs/vrf_templates/Site1-TSMC_50000_bluevrf.json")
    # delete_VRF(fabric="Site1-TSMC", vrf_name="bluevrf")
    # get_VRF_attachment(fabric="Site1-TSMC", vrf_dir="vrfs", vrfname="", filter="", range="0-9")
    pass