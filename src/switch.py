import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from utils import *
import json
from dotenv import load_dotenv

def getSwitches(fabric, switch_dir="switches"):
    # range = show the switches from 0 to {range}
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/inventory/switchesByFabric")
    headers = getAPIKeyHeader()
    r = requests.get(url, headers=headers, verify=False)
    checkStatusCode(r)

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

def deleteSwitch(fabric, serial_number):
    headers = getAPIKeyHeader()
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/switches/{serial_number}")
    r = requests.delete(url, headers=headers, verify=False)
    checkStatusCode(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def discoverSwitch(fabric, filename):
    load_dotenv()
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/inventory/discover")
    headers = getAPIKeyHeader()
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
    checkStatusCode(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def changeDiscoveryIP(fabric, serial_number, new_ip):
    headers = getAPIKeyHeader()
    headers['Content-Type'] = 'application/json'
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/inventory/discoveryIP")
    payload = {
        "serialNumber": serial_number,
        "ipAddress": new_ip
    }
    r = requests.put(url, headers=headers, json=payload, verify=False)
    checkStatusCode(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

def rediscoverDevice(fabric, serial_number):
    headers = getAPIKeyHeader()
    url = getURL(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/inventory/rediscover/{serial_number}")

    r = requests.post(url, headers=headers, verify=False)
    checkStatusCode(r)
    print(f"Status Code: {r.status_code}")
    print(f"Message: {r.text}")

if __name__ == "__main__":
    # getSwitches(fabric="Site1-TSMC", switch_dir="switches")
    # deleteSwitch(fabric="Site1-TSMC", serial_number="9J9UDVX8MMA")
    # discoverSwitch(fabric="Site1-TSMC", filename="switches/discover/Site1-L3-73.json")
    changeDiscoveryIP(fabric="Site1-TSMC", serial_number="9J9UDVX8MMA", new_ip="10.192.195.73")
    # rediscoverDevice(fabric="Site1-TSMC", serial_number="9J9UDVX8MMA")