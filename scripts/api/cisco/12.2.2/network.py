import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from utils import *
import json

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

def create_network(filename, network_template_config_file=""):
    headers = get_api_key_header()
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
    network_template_config_str = parse_template_config(network_template_config_file) if network_template_config_file else ""
    payload["networkTemplateConfig"] = network_template_config_str
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{payload['fabric']}/networks")
    r = requests.post(url, headers=headers, json=payload, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def update_network(filename, network_template_config_file=""):
    headers = get_api_key_header()
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
    network_template_config_str = parse_template_config(network_template_config_file) if network_template_config_file else ""
    payload["networkTemplateConfig"] = network_template_config_str
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{payload['fabric']}/networks/{payload['networkName']}")
    r = requests.put(url, headers=headers, json=payload, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def delete_network(fabric, network_name):
    headers = get_api_key_header()
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks/{network_name}")
    r = requests.delete(url, headers=headers, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

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

def update_network_attachment(filename):
    headers = get_api_key_header()
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
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks/{network_name}/attachments")
    
    r = requests.post(url, headers=headers, json=payload, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def preview_networks(fabric, network_names):
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    # Preview networks
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks/preview")
    query_params = {
        "network-names": network_names
    }
    
    r = requests.get(url, headers=headers, params=query_params, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def deploy_networks(fabric, network_names):
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    # Deploy networks
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks/deployments")
    payload = {
        "networkNames": network_names
    }
    
    r = requests.post(url, headers=headers, json=payload, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

if __name__ == "__main__":
    # get_networks(fabric="Site1-Greenfield", network_dir="networks", network_template_config_dir="networks/network_templates", network_filter="", range=10)
    # get_network(fabric="Site1-Greenfield", network_name="bluenet1", network_dir="networks", network_template_config_dir="networks/network_templates")
    # get_networks(fabric="Site1-TSMC", network_dir="networks", network_template_config_dir="networks/network_templates", network_filter="", range=0)
    # create_network(filename="networks/Site1-TSMC_30000_bluenet1.json", network_template_config_file="networks/network_templates/Site1-TSMC_30000_bluenet1.json")
    # update_network(filename="networks/Site1-TSMC_30000_bluenet1.json", network_template_config_file="networks/network_templates/Site1-TSMC_30000_bluenet1.json")
    # delete_network(fabric="Site1-TSMC", network_name="bluenet1")
    # update_network_attachment(filename="networks/attachments/test.json")
    # get_network_attachment(fabric="Site1-Greenfield", network_dir="networks", networkname="bluenet2")
    preview_networks(fabric="Site1-Greenfield", network_names="bluenet2")
    # deploy_networks(fabric="Site1-Greenfield", network_names="bluenet2")
    get_network_attachment(fabric="Site1-Greenfield", network_dir="networks", networkname="bluenet2")