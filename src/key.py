import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from utils import *

from dotenv import load_dotenv

def login():
    load_dotenv()
    USERNAME = os.getenv("LOGIN_USERNAME")
    PASSWORD = os.getenv("LOGIN_PASSWORD")
    url = getURL("/login")

    payload = {
        "userName" : USERNAME,
        "userPasswd": PASSWORD,
        "domain": "DefaultAuth"
    }

    r = requests.post(url=url, json=payload, verify=False)

    checkStatusCode(r)
    json_data = r.json()
    jwttoken = json_data.get("jwttoken")

    return jwttoken

def addAPIKey(token):
    headers = {
        'Cookie': f'AuthCookie={token}'
    }

    payload = {}
    url = getURL("/api/config/addapikey")
    r = requests.post(url, headers=headers, json=payload, verify=False)

    checkStatusCode(r)
    print(r.json())

def getAPIKey(token):
    url = getURL("/api/config/dn/userapikey/local-admin?showPassword=yes")
    headers = {
        'Cookie': f'AuthCookie={token}'
    }
    r = requests.get(url, headers=headers, verify=False)

    checkStatusCode(r)

    response_json = r.json()
    api_keys = response_json.get("apiKeys", [])
    if api_keys:
        return api_keys[0].get("key", "")
    else:
        print("No api keys")

def generateAPIKey():
    token = login()
    # addAPIKey(token)
    api_key = getAPIKey(token)
    print(f"API key: {api_key}")

if __name__ == "__main__":
    generateAPIKey()