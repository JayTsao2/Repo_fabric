from dotenv import load_dotenv
import sys
import os
import json

management_IP = 'https://10.192.195.20'

def get_url(api):
    return f"{management_IP}{api}"

def get_api_key_header():
    load_dotenv()
    NDFC_API_KEY = os.getenv("NDFC_API_KEY")

    headers = {
        'X-Nd-Apikey': NDFC_API_KEY,
        'X-Nd-Username': 'admin',
    }
    return headers

def check_status_code(r):
    if r.status_code != 200:
        print(f"Request Failed, Status code: {r.status_code}")
        print(f"Error Message: {r.text}")
        sys.exit(1)

def parse_template_config(filename) -> str:
    # Parse the json from the file and serialize it into a string
    try:
        with open(filename, "r") as file:
            data = json.load(file)
        json_string = json.dumps(data)
        return json_string
    except Exception as e:
        print(f"Error: {e}")
        return ""
    
def parse_freeform_config(filename) -> str:
    # Parse the free form config from the file and serialize it into a string
    try:
        with open(filename, "r") as file:
            data = file.read()
        if "Banner.sh" in filename:
            data = "`" + data + "`"
        return data
    except Exception as e:
        print(f"Error: {e}")
        return ""