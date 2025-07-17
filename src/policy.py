import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from utils import *
import json

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

if __name__ == "__main__":
    # getPolicyBySerialNumber("9LT3A74X1AS", "policies")
    getPolicyByID("188510", "policies")