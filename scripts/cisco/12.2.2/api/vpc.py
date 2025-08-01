"""
VPC API Module

This module handles all VPC-related API operations including:
- Creating VPC pairs between switches
- Deleting VPC pairs
- Setting VPC policies
- Deleting VPC policies
"""

import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3
urllib3.disable_warnings(InsecureRequestWarning)
from .utils import *


def create_vpc_pair(peer_one_id, peer_two_id, use_virtual_peerlink=False):
    """Create VPC pair using the vpcpair API endpoint."""
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/vpcpair")
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    payload = {
        "peerOneId": peer_one_id,
        "peerTwoId": peer_two_id,
        "useVirtualPeerlink": use_virtual_peerlink
    }
    
    r = requests.post(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name="Create VPC Pair")


def delete_vpc_pair(serial_number):
    """Delete VPC pair using the vpcpair API endpoint with serial number."""
    url = get_url(f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/vpcpair?serialNumber={serial_number}")
    headers = get_api_key_header()
    
    r = requests.delete(url, headers=headers, verify=False)
    return check_status_code(r, operation_name="Delete VPC Pair")


def delete_vpc_policy(vpc_name, serial_numbers):
    """Delete VPC policy using the interface markdelete endpoint."""
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface/markdelete")
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    payload = [{
        "ifName": vpc_name,
        "serialNumber": serial_numbers
    }]
    r = requests.delete(url, headers=headers, json=payload, verify=False)
    return check_status_code(r, operation_name="Delete VPC Policy")


def set_vpc_policy(policy_data):
    """Set VPC policy using the interface API endpoint."""
    url = get_url("/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface")
    headers = get_api_key_header()
    headers['Content-Type'] = 'application/json'
    
    r = requests.post(url, headers=headers, json=policy_data, verify=False)
    return check_status_code(r, operation_name="Set VPC Policy")
