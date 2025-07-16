from dotenv import load_dotenv
import sys
import os
import json

management_IP = 'https://10.192.195.20'

def getURL(api):
    return f"{management_IP}{api}"

def getAPIKeyHeader():
    load_dotenv()
    NDFC_API_KEY = os.getenv("NDFC_API_KEY")

    headers = {
        'X-Nd-Apikey': NDFC_API_KEY,
        'X-Nd-Username': 'admin',
    }
    return headers

def checkStatusCode(r):
    if r.status_code != 200:
        print(f"Request Failed, Status code: {r.status_code}")
        print(f"Error Message: {r.text}")
        sys.exit(1)

def parseTemplateConfig(filename) -> str:
    # Parse the json from the file and serialize it into a string
    try:
        with open(filename, "r") as file:
            data = json.load(file)
        json_string = json.dumps(data)
        return json_string
    except Exception as e:
        print(f"Error: {e}")
        return ""