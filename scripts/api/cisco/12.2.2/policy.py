import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from utils import *
import json

def check_config_exists(json_data):
    # return True if the json data has a "nvPairs" key, and inside it has a "CONF" key
    if "nvPairs" in json_data and "CONF" in json_data["nvPairs"]:
        return True
    return False

def save_policy_config(data, policy_dir="policies"):
    # Save the policy config to a file
    serial_number = data.get("serialNumber", "unknown")
    policy_id = data.get("policyId", "unknown")
    filename = f"{policy_dir}/{policy_id}.json"

    if not os.path.exists(policy_dir):
        os.makedirs(policy_dir)
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
        print(f"{policy_id} is saved to {filename}")

    if not check_config_exists(data):
        return
    
    if not os.path.exists(f"{policy_dir}/FreeForm"):
        os.makedirs(f"{policy_dir}/FreeForm")

    freeform_config = data["nvPairs"]["CONF"]
    template_name = data.get("templateName", "")
    freeform_filename = f"{policy_dir}/FreeForm/{policy_id}_{template_name}.sh"
    with open(freeform_filename, "w") as f:
        f.write(freeform_config)
        print(f"Freeform config for {policy_id} is saved to {freeform_filename}")

def get_policy_by_serial_number(serial_number, policy_dir="policies"):
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/switches")
    headers = get_api_key_header()
    params = {"serialNumber": serial_number}
    r = requests.get(url, headers=headers, params=params, verify=False)
    check_status_code(r)

    policies = r.json()
    # if the directory does not exist, create it
    if not os.path.exists(policy_dir):
        os.makedirs(policy_dir)
    for policy in policies:
        # Save each policy to a file
        save_policy_config(policy, policy_dir)
        
def get_policy_by_id(id, policy_dir="policies"):
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/{id}")
    headers = get_api_key_header()
    r = requests.get(url, headers=headers, verify=False)
    check_status_code(r)
    if not os.path.exists(policy_dir):
        os.makedirs(policy_dir)

    save_policy_config(r.json(), policy_dir)

def update_policy_by_file(filename):
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    # Update a policy with the data from the file
    try:
        with open(filename, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"File {filename} not found!")
        exit()
    except Exception as e:
        print(f"Error: {e}")
        exit()
    payload = data
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/{id}")
    r = requests.put(url, headers=headers, json=payload, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def delete_policy(id):
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/POLICY-{id}")
    headers = get_api_key_header()
    r = requests.delete(url, headers=headers, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

if __name__ == "__main__":
    # get_policy_by_serial_number("9LT3A74X1AS", "policies")
    get_policy_by_id("188990", "policies")
    # update_policy_by_file("policies/POLICY-54260.json")
    # delete_policy("210860")