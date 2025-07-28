import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3
urllib3.disable_warnings(InsecureRequestWarning)
from .utils import *
import json
from dotenv import load_dotenv

def get_switches(fabric, switch_dir="switches"):
    # range = show the switches from 0 to {range}
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/inventory/switchesByFabric")
    headers = get_api_key_header()
    r = requests.get(url, headers=headers, verify=False)
    check_status_code(r)

    switches = r.json()
    # if the directory does not exist, create it
    if not os.path.exists(switch_dir):
        os.makedirs(switch_dir)
    # Save switches to a file, switches is an array of switch objects
    for switch in switches:
        serial_number = switch.get("serialNumber", "unknown")
        hostname = switch.get("hostName", "unknown")
        filename = f"{switch_dir}/{fabric}_{serial_number}_{hostname}.json"
        with open(filename, "w") as f:
            json.dump(switch, f, indent=4)
            print(f"Switch config for {hostname} (ID: {serial_number}) is saved to {filename}")

def delete_switch(fabric, serial_number):
    headers = get_api_key_header()
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/switches/{serial_number}")
    r = requests.delete(url, headers=headers, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def discover_switch_from_payload(fabric, payload):
    """Discover switch using provided payload data."""
    load_dotenv()
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/inventory/discover")
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    # Set password from environment
    payload["password"] = os.getenv("SWITCH_PASSWORD") 
    
    try:
        r = requests.post(url, headers=headers, json=payload, verify=False)
        check_status_code(r)
        return True
    except Exception as e:
        print(f"Error discovering switch: {e}")
        return False

def discover_switch(fabric, filename):
    load_dotenv()
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/inventory/discover")
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
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

    payload["password"] = os.getenv("SWITCH_PASSWORD") 
    r = requests.post(url, headers=headers, json=payload, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def change_discovery_ip(fabric, serial_number, new_ip):
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/inventory/discoveryIP")
    payload = {
        "serialNumber": serial_number,
        "ipAddress": new_ip
    }
    r = requests.put(url, headers=headers, json=payload, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def rediscover_device(fabric, serial_number):
    headers = get_api_key_header()
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/inventory/rediscover/{serial_number}")

    r = requests.post(url, headers=headers, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def get_config_preview(fabric, serial_number):
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/config-preview/{serial_number}")
    headers = get_api_key_header()
    r = requests.get(url, headers=headers, verify=False)
    check_status_code(r)
    
    data = r.json()
    filename = f"switches/{fabric}_{serial_number}_config_preview.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
        print(f"Config preview for {serial_number} is saved to {filename}")
    for switch in data:
        parsePendingConfig(switch["pendingConfig"], f"switches/{fabric}_{serial_number}_pending_config.sh")

def get_config_diff(fabric, serial_number):
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/config-diff/{serial_number}")
    headers = get_api_key_header()
    r = requests.get(url, headers=headers, verify=False)
    check_status_code(r)
    data = r.json()
    # filename = f"switches/{fabric}_{serial_number}_config_diff.json"
    # with open(filename, "w") as f:
    #     json.dump(data, f, indent=4)
    #     print(f"Config diff for {serial_number} is saved to {filename}")
    parse_config_diff(data["diff"], f"switches/{fabric}_{serial_number}_config_diff.sh")

def parse_config_diff(data, filename):
    """
    Parse config diff data and write to file in diff format
    data: JSON array with format [["EQUAL"|"INSERT"|"DELETE", "line1", "line2"], ...]
    filename: output file path
    """
    try:
        with open(filename, "w") as f:
            for item in data:
                if len(item) != 3:
                    continue
                
                operation, line1, line2 = item
                
                if operation == "EQUAL":
                    # For EQUAL operations, show the line without prefix
                    if line1:
                        f.write(f"    {line1}\n")
                elif operation == "INSERT":
                    # For INSERT operations, show with + prefix
                    if line2:
                        f.write(f"[+] {line2}\n")
                elif operation == "DELETE":
                    # For DELETE operations, show with - prefix
                    if line1:
                        f.write(f"[-] {line1}\n")
        
        print(f"Config diff parsed and saved to {filename}")
        
    except Exception as e:
        print(f"Error parsing config diff: {e}")

def parsePendingConfig(data, filename):
    """
    Parse pending config data and write to file
    data: JSON array with configuration lines
    filename: output file path
    """
    try:
        with open(filename, "w") as f:
            for line in data:
                f.write(f"{line}\n")
        
        print(f"Pending config parsed and saved to {filename}")
        
    except Exception as e:
        print(f"Error parsing pending config: {e}")

def deploy_switch_config(fabric, serial_number):
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/config-deploy/{serial_number}")
    headers = get_api_key_header()
    r = requests.post(url, headers=headers, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def set_switch_role(serial_number, role):
    """Set switch role using the switches/roles API endpoint."""
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/switches/roles")
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    payload = [
        {
            "serialNumber": serial_number,
            "role": role
        }
    ]
    
    r = requests.post(url, headers=headers, json=payload, verify=False)
    check_status_code(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")


if __name__ == "__main__":
    # get_switches(fabric="Site1", switch_dir="switches")
    delete_switch(fabric="Site1-TSMC", serial_number="9J9UDVX8MMA")
    # discover_switch(fabric="Site1-TSMC", filename="switches/discover/Site1-L3-73.json")
    # change_discovery_ip(fabric="Site1-TSMC", serial_number="9J9UDVX8MMA", new_ip="10.192.195.73")
    # rediscover_device(fabric="Site1-TSMC", serial_number="9J9UDVX8MMA")
    # get_config_preview(fabric="Site1", serial_number="9W4GBLXU5CR")
    # get_config_preview(fabric="Site1", serial_number="95H3IT6BGM0")
    # get_config_diff(fabric="ISN_DCI", serial_number="9IN4SP84L7L")
    # deploy_switch_config(fabric="Site1", serial_number="9W4GBLXU5CR")
