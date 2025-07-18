import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from utils import *
import json

def getFabrics():
    url = getURL("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics")
    headers = getAPIKeyHeader()

    r = requests.get(url=url, headers=headers, verify =False)
    checkStatusCode(r)
    

    fabrics = r.json()
    # print(fabrics)
    with open("fabrics.json", "w") as f:
        json.dump(fabrics, f, indent=4)

def getFabric(fabric, fabric_dir="fabrics"):
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}")
    
    headers = getAPIKeyHeader()

    r = requests.get(url=url, headers=headers, verify = False)
    checkStatusCode(r)
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

def deleteFabric(fabric):
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}")

    headers = getAPIKeyHeader()
    r = requests.delete(url=url, headers=headers, verify=False)
    checkStatusCode(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def createFabric(filename, template_name, leaf_freeform_config_file="", spine_freeform_config_file="", aaa_freeform_config_file=""):
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

    payload["EXTRA_CONF_LEAF"] = parseFreeFormConfig(leaf_freeform_config_file) if leaf_freeform_config_file else ""
    payload["EXTRA_CONF_SPINE"] = parseFreeFormConfig(spine_freeform_config_file) if spine_freeform_config_file else ""
    payload["AAA_SERVER_CONF"] = parseFreeFormConfig(aaa_freeform_config_file) if aaa_freeform_config_file else ""
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/{template_name}")

    headers = getAPIKeyHeader()
    headers['Content-Type'] = 'application/json'
    r = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)
    checkStatusCode(r)

    print(f"Fabric {fabric} has been successfully created!")

def updateFabric(filename, template_name, leaf_freeform_config_file="", spine_freeform_config_file="", aaa_freeform_config_file=""):
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
    
    payload["EXTRA_CONF_LEAF"] = parseFreeFormConfig(leaf_freeform_config_file) if leaf_freeform_config_file else ""
    payload["EXTRA_CONF_SPINE"] = parseFreeFormConfig(spine_freeform_config_file) if spine_freeform_config_file else ""
    payload["AAA_SERVER_CONF"] = parseFreeFormConfig(aaa_freeform_config_file) if aaa_freeform_config_file else ""
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/{template_name}")

    headers = getAPIKeyHeader()
    headers['Content-Type'] = 'application/json'
    r = requests.put(url, headers=headers, data=json.dumps(payload), verify=False)
    checkStatusCode(r)

    print(f"Fabric {fabric} has been successfully updated!")

def recalculateConfig(fabric):
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/config-save")
    headers = getAPIKeyHeader()
    r = requests.post(url, headers=headers, verify=False)
    checkStatusCode(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def deployFabricConfig(fabric):
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/config-deploy")
    headers = getAPIKeyHeader()
    r = requests.post(url, headers=headers, verify=False)
    checkStatusCode(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

if __name__ == "__main__":
    # getFabrics()
    # getFabric("Site1-Greenfield", "fabrics")
    # createFabric("fabrics/Site1-TSMC.json", "Easy_Fabric", "fabrics/Site1-TSMC_FreeForm/Leaf_FreeForm_Config.sh", "fabrics/Site1-TSMC_FreeForm/Spine_FreeForm_Config.sh", "fabrics/Site1-TSMC_FreeForm/AAA_Freeform_Config.sh")
    # updateFabric("fabrics/Site1-TSMC.json", "Easy_Fabric", "fabrics/Site1-TSMC_FreeForm/Leaf_FreeForm_Config.sh", "fabrics/Site1-TSMC_FreeForm/Spine_FreeForm_Config.sh", "fabrics/Site1-TSMC_FreeForm/AAA_Freeform_Config.sh")
    # deleteFabric("Site1-TSMC")
    recalculateConfig(fabric="Site1")
    deployFabricConfig(fabric="Site1")
