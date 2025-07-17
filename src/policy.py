import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from utils import *
import json

def checkConfigExists(json_data):
    # return True if the json data has a "nvPairs" key, and inside it has a "CONF" key
    if "nvPairs" in json_data and "CONF" in json_data["nvPairs"]:
        return True
    return False

def getPolicyBySerialNumber(serial_number, policy_dir="policies"):
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/switches")
    headers = getAPIKeyHeader()
    params = {"serialNumber": serial_number}
    r = requests.get(url, headers=headers, params=params, verify=False)
    checkStatusCode(r)

    policies = r.json()
    # if the directory does not exist, create it
    if not os.path.exists(policy_dir):
        os.makedirs(policy_dir)
    for policy in policies:
        # Save each policy to a file
        policy_id = policy.get("policyId", "unknown")
        filename = f"{policy_dir}/{policy_id}.json"
        with open(filename, "w") as f:
            json.dump(policy, f, indent=4)
            print(f"Policy config for {serial_number} (ID: {policy_id}) is saved to {filename}")
        if checkConfigExists(policy):
            if not os.path.exists(f"{policy_dir}/FreeForm"):
                os.makedirs(f"{policy_dir}/FreeForm")
            freeform_config = policy["nvPairs"]["CONF"]
            template_name = policy.get("templateName", "")
            freeform_filename = f"{policy_dir}/FreeForm/{policy_id}_{template_name}.sh"
            with open(freeform_filename, "w") as ff:
                ff.write(freeform_config)
                print(f"Freeform config for {serial_number} (ID: {policy_id}) is saved to {freeform_filename}")

def getPolicyByID(id, policy_dir="policies"):
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/{id}")
    headers = getAPIKeyHeader()
    r = requests.get(url, headers=headers, verify=False)
    checkStatusCode(r)
    if not os.path.exists(policy_dir):
        os.makedirs(policy_dir)

    policy = r.json()
    policy_id = policy.get("policyId", "unknown")
    # Save the policy to a file
    filename = f"{policy_dir}/{policy_id}.json"
    with open(filename, "w") as f:
        json.dump(policy, f, indent=4)
        print(f"Policy config for ID: {policy_id} is saved to {filename}")

def updatePolicyByFile(filename):
    headers = getAPIKeyHeader()
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
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/{id}")
    r = requests.put(url, headers=headers, json=payload, verify=False)
    checkStatusCode(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def deletePolicy(id):
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/POLICY-{id}")
    headers = getAPIKeyHeader()
    r = requests.delete(url, headers=headers, verify=False)
    checkStatusCode(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

if __name__ == "__main__":
    getPolicyBySerialNumber("9LT3A74X1AS", "policies")
    # getPolicyByID("54270", "policies")
    # updatePolicyByFile("policies/POLICY-54260.json")
    # deletePolicy("210860")