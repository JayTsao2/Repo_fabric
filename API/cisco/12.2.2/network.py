import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from utils import *
import json

def getNetworks(fabric, network_dir="networks", network_template_config_dir="networks/network_templates", network_filter="", range=0):
    # range = show the networks from 0 to {range}
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks")
    headers = getAPIKeyHeader()
    headers["range"] = f"0-{range}"
    query_params = {}
    if network_filter != "":
        query_params["filter"] = network_filter
    r = requests.get(url, headers=headers, params=query_params, verify=False)
    checkStatusCode(r)

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

def getNetwork(fabric, network_name, network_dir="networks", network_template_config_dir="networks/network_templates"):
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks/{network_name}")
    headers = getAPIKeyHeader()
    r = requests.get(url, headers=headers, verify=False)
    checkStatusCode(r)

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

def createNetwork(filename, network_template_config_file=""):
    headers = getAPIKeyHeader()
    headers['Content-Type'] = 'application/json'
    
    # Create a network with the data from the file
    try:
        with open(filename, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"File {filename} not found!")
        exit()
    except Exception as e:
        print(f"Error: {e}")
    payload = data
    network_template_config_str = parseTemplateConfig(network_template_config_file) if network_template_config_file else ""
    payload["networkTemplateConfig"] = network_template_config_str
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{payload['fabric']}/networks")
    r = requests.post(url, headers=headers, json=payload, verify=False)
    checkStatusCode(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def updateNetwork(filename, network_template_config_file=""):
    headers = getAPIKeyHeader()
    headers['Content-Type'] = 'application/json'
    
    # Update a network with the data from the file
    try:
        with open(filename, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"File {filename} not found!")
        exit()
    except Exception as e:
        print(f"Error: {e}")
    payload = data
    network_template_config_str = parseTemplateConfig(network_template_config_file) if network_template_config_file else ""
    payload["networkTemplateConfig"] = network_template_config_str
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{payload['fabric']}/networks/{payload['networkName']}")
    r = requests.put(url, headers=headers, json=payload, verify=False)
    checkStatusCode(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def deleteNetwork(fabric, network_name):
    headers = getAPIKeyHeader()
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks/{network_name}")
    r = requests.delete(url, headers=headers, verify=False)
    checkStatusCode(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def getNetworkAttachment(fabric, network_dir="networks", networkname=""):
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks/{networkname}/attachments")
    headers = getAPIKeyHeader()
    r = requests.get(url, headers=headers, verify=False)
    checkStatusCode(r)

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

def updateNetworkAttachment(filename):
    headers = getAPIKeyHeader()
    headers['Content-Type'] = 'application/json'
    
    # Update a network attachment with the data from the file
    try:
        with open(filename, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"File {filename} not found!")
        exit()
    except Exception as e:
        print(f"Error: {e}")
    
    payload = data
    fabric = payload.get("fabric", "unknown")
    network_name = payload.get("networkName", "unknown")
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks/{network_name}/attachments")
    
    r = requests.post(url, headers=headers, json=payload, verify=False)
    checkStatusCode(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def previewNetworks(fabric, network_names):
    headers = getAPIKeyHeader()
    headers['Content-Type'] = 'application/json'
    
    # Preview networks
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks/preview")
    query_params = {
        "network-names": network_names
    }
    
    r = requests.get(url, headers=headers, params=query_params, verify=False)
    checkStatusCode(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def deployNetworks(fabric, network_names):
    headers = getAPIKeyHeader()
    headers['Content-Type'] = 'application/json'
    
    # Deploy networks
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks/deployments")
    payload = {
        "networkNames": network_names
    }
    
    r = requests.post(url, headers=headers, json=payload, verify=False)
    checkStatusCode(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

if __name__ == "__main__":
    # getNetworks(fabric="Site1-Greenfield", network_dir="networks", network_template_config_dir="networks/network_templates", network_filter="", range=10)
    # getNetwork(fabric="Site1-Greenfield", network_name="bluenet1", network_dir="networks", network_template_config_dir="networks/network_templates")
    # getNetworks(fabric="Site1-TSMC", network_dir="networks", network_template_config_dir="networks/network_templates", network_filter="", range=0)
    # createNetwork(filename="networks/Site1-TSMC_30000_bluenet1.json", network_template_config_file="networks/network_templates/Site1-TSMC_30000_bluenet1.json")
    # updateNetwork(filename="networks/Site1-TSMC_30000_bluenet1.json", network_template_config_file="networks/network_templates/Site1-TSMC_30000_bluenet1.json")
    # deleteNetwork(fabric="Site1-TSMC", network_name="bluenet1")
    # updateNetworkAttachment(filename="networks/attachments/test.json")
    # getNetworkAttachment(fabric="Site1-Greenfield", network_dir="networks", networkname="bluenet2")
    previewNetworks(fabric="Site1-Greenfield", network_names="bluenet2")
    # deployNetworks(fabric="Site1-Greenfield", network_names="bluenet2")
    getNetworkAttachment(fabric="Site1-Greenfield", network_dir="networks", networkname="bluenet2")