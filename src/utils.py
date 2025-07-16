from dotenv import load_dotenv
import sys
import os

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