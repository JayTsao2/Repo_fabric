import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from utils import *
import json

def get_fabrics():
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics")
    headers = get_api_key_header()

    r = requests.get(url=url, headers=headers, verify =False)
    check_status_code(r)
    

    fabrics = r.json()
    # print(fabrics)
    with open("fabrics.json", "w") as f:
        json.dump(fabrics, f, indent=4)

def get_fabric(fabric, fabric_dir="fabrics"):
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}")
    
    headers = get_api_key_header()

    r = requests.get(url=url, headers=headers, verify = False)
    check_status_code(r)
    try: 
        data = r.json()
        if not os.path.exists(fabric_dir):
            os.makedirs(fabric_dir)
        filename = f"{fabric_dir}/{fabric}.json"
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
            print(f"Fabric {fabric} data is saved to {filename}")
    except Exception as e:
        print(f"Error: {e}")

def delete_fabric(fabric):
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}")

    headers = get_api_key_header()
    r = requests.delete(url=url, headers=headers, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def create_fabric(filename, template_name, leaf_freeform_config_file="", spine_freeform_config_file="", aaa_freeform_config_file=""):
    try:
        with open(filename, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"File {filename} not found!")
        exit()
    except Exception as e:
        print(f"Error: {e}")
        exit()
    fabric= data.get("fabricName")
    payload = data["nvPairs"]
    invalid_fields = ["USE_LINK_LOCAL", "ISIS_OVERLOAD_ENABLE", "ISIS_P2P_ENABLE","PNP_ENABLE_INTERNAL", "DOMAIN_NAME_INTERNAL"]
    for key in invalid_fields:
        if key in payload:
            # print(f"Removing {key} in payload...")
            del payload[key]

    payload["EXTRA_CONF_LEAF"] = parse_freeform_config(leaf_freeform_config_file) if leaf_freeform_config_file else ""
    payload["EXTRA_CONF_SPINE"] = parse_freeform_config(spine_freeform_config_file) if spine_freeform_config_file else ""
    payload["AAA_SERVER_CONF"] = parse_freeform_config(aaa_freeform_config_file) if aaa_freeform_config_file else ""
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/{template_name}")

    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    r = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)
    check_status_code(r)

    print(f"Fabric {fabric} has been successfully created!")

def update_fabric(filename, template_name, leaf_freeform_config_file="", spine_freeform_config_file="", aaa_freeform_config_file=""):
    try:
        with open(filename, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"File {filename} not found!")
        exit()
    except Exception as e:
        print(f"Error: {e}")
        exit()
    fabric = data.get("fabricName")
    payload = data["nvPairs"]
    invalid_fields = ["USE_LINK_LOCAL", "ISIS_OVERLOAD_ENABLE", "ISIS_P2P_ENABLE","PNP_ENABLE_INTERNAL", "DOMAIN_NAME_INTERNAL"]
    for key in invalid_fields:
        if key in payload:
            del payload[key]
    
    payload["EXTRA_CONF_LEAF"] = parse_freeform_config(leaf_freeform_config_file) if leaf_freeform_config_file else ""
    payload["EXTRA_CONF_SPINE"] = parse_freeform_config(spine_freeform_config_file) if spine_freeform_config_file else ""
    payload["AAA_SERVER_CONF"] = parse_freeform_config(aaa_freeform_config_file) if aaa_freeform_config_file else ""
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/{template_name}")

    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    r = requests.put(url, headers=headers, data=json.dumps(payload), verify=False)
    check_status_code(r)

    print(f"Fabric {fabric} has been successfully updated!")

def recalculate_config(fabric):
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/config-save")
    headers = get_api_key_header()
    r = requests.post(url, headers=headers, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def deploy_fabric_config(fabric):
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/config-deploy")
    headers = get_api_key_header()
    r = requests.post(url, headers=headers, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

if __name__ == "__main__":
    # get_fabrics()
    # get_fabric("Site1-Greenfield", "fabrics")
    # create_fabric("fabrics/Site1-TSMC.json", "Easy_Fabric", "fabrics/Site1-TSMC_FreeForm/Leaf_FreeForm_Config.sh", "fabrics/Site1-TSMC_FreeForm/Spine_FreeForm_Config.sh", "fabrics/Site1-TSMC_FreeForm/AAA_Freeform_Config.sh")
    # update_fabric("fabrics/Site1-TSMC.json", "Easy_Fabric", "fabrics/Site1-TSMC_FreeForm/Leaf_FreeForm_Config.sh", "fabrics/Site1-TSMC_FreeForm/Spine_FreeForm_Config.sh", "fabrics/Site1-TSMC_FreeForm/AAA_Freeform_Config.sh")
    # delete_fabric("Site1-TSMC")
    recalculate_config(fabric="Site1")
    deploy_fabric_config(fabric="Site1")
