import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3
urllib3.disable_warnings(InsecureRequestWarning)
from .utils import *
import json

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

def create_VRF(filename, vrf_template_config_file=""):
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    # Create a vrf with the data from the file
    try:
        with open(filename, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"File {filename} not found!")
        exit()
    except Exception as e:
        print(f"Error: {e}")

    payload = data
    vrf_template_config_str = parse_template_config(vrf_template_config_file) if vrf_template_config_file else ""
    payload["vrfTemplateConfig"] = vrf_template_config_str
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{payload["fabric"]}/vrfs")

    print(f"URL: {url}")
    r = requests.post(url, headers=headers, json=payload, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def update_VRF(filename, vrf_template_config_file=""):
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    # Update a vrf with the data from the file
    try:
        with open(filename, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"File {filename} not found!")
        exit()
    except Exception as e:
        print(f"Error: {e}")
    
    payload = data
    vrf_template_config_str = parse_template_config(vrf_template_config_file) if vrf_template_config_file else ""
    payload["vrfTemplateConfig"] = vrf_template_config_str
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{payload['fabric']}/vrfs/{payload['vrfName']}")
    r = requests.put(url, headers=headers, json=payload, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def delete_VRF(fabric, vrf_name):
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/vrfs/{vrf_name}")
    headers = get_api_key_header()
    r = requests.delete(url, headers=headers, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def get_VRF_attachment(fabric, vrf_dir="vrfs", vrfname="", filter="", range="0-9"):
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/vrfs/attachments")
    headers = get_api_key_header()
    headers["Range"] = range
    query_params = {
        "vrf-names": vrfname,
        "filter": filter,
        "switch-name": ""
    }
    if filter:
        headers["filter"] = filter
    r = requests.get(url, headers=headers, params=query_params, verify=False)
    check_status_code(r)

    attachments = r.json()
    if not os.path.exists(vrf_dir):
        os.makedirs(vrf_dir)
    if not os.path.exists(f"{vrf_dir}/attachments"):
        os.makedirs(f"{vrf_dir}/attachments")
    for attachment in attachments:
        attachment_vrfname = attachment.get("vrfName", "unknown")
        filename = f"{vrf_dir}/attachments/{fabric}_{attachment_vrfname}.json"
        with open(filename, "w") as f:
            json.dump(attachment, f, indent=4)
            print(f"VRF attachments for {attachment_vrfname} are saved to {filename}")

def update_VRF_attachment(filename):
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    # Update a vrf attachment with the data from the file
    try:
        with open(filename, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"File {filename} not found!")
        exit()
    except Exception as e:
        print(f"Error: {e}")
    
    payload = data
    fabric = payload[0].get("lanAttachList", [{}])[0].get("fabric", "unknown")
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/vrfs/attachments")
    r = requests.post(url, headers=headers, json=payload, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

if __name__ == "__main__":
    # get_VRFs(fabric="Site1-Greenfield", vrf_dir="vrfs", vrf_template_config_dir="vrfs/vrf_templates", vrf_filter="vrfId==50000", range=0)
    # get_VRFs(fabric="Site1-TSMC", vrf_dir="vrfs", vrf_template_config_dir="vrfs/vrf_templates", vrf_filter="", range=0)
    # create_VRF(filename="vrfs/Site1-TSMC_50000_bluevrf.json", vrf_template_config_file="vrfs/vrf_templates/Site1-TSMC_50000_bluevrf.json")
    # update_VRF(filename="vrfs/Site1-TSMC_50000_bluevrf.json", vrf_template_config_file="vrfs/vrf_templates/Site1-TSMC_50000_bluevrf.json")
    # delete_VRF(fabric="Site1-TSMC", vrf_name="bluevrf")
    # get_VRF_attachment(fabric="Site1-TSMC", vrf_dir="vrfs", vrfname="", filter="", range="0-9")
    update_VRF_attachment(filename="vrfs/vrf_attach_list.json")