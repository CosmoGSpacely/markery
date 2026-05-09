#!/usr/bin/env python3
"""
USPTO TSDR API Client

This script demonstrates how to access USPTO Trademark Status and Document Retrieval (TSDR) data.

Requirements:
- Python 3.6+
- requests library
- A valid USPTO API key (obtain from https://account.uspto.gov/api-manager/)

Usage:
1. Set your API key in the USPTO_API_KEY environment variable or in a .env file.
2. Run the script: python tsdr_client.py

Note: Rate limits apply (60 requests/minute, 4 for PDF/ZIP/multi-case).
"""

import json
import os
import sys

import requests

from dotenv import load_dotenv

load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("USPTO_API_KEY")
if not API_KEY:
    print("Please set the USPTO_API_KEY environment variable with your API key.")
    print("Obtain a key from: https://account.uspto.gov/api-manager/")
    sys.exit(1)

# Base URL for TSDR API
BASE_URL = "https://tsdrapi.uspto.gov"

# Headers for API requests
def get_request_headers(accept="application/json"):
    return {
        "USPTO-API-KEY": API_KEY,
        "Accept": accept,
    }

def get_case_status(serial_number):
    """
    Get trademark case status for a given serial number.

    Args:
        serial_number (str): Serial number (e.g., '78787878')

    Returns:
        dict: JSON response from API
    """
    url = f"{BASE_URL}/ts/cd/casestatus/sn{serial_number}/info"
    response = requests.get(url, headers=get_request_headers())

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

def get_last_update(serial_number):
    """
    Get last update time for a case.

    Args:
        serial_number (str): Serial number

    Returns:
        dict: JSON response
    """
    url = f"{BASE_URL}/last-update/info.json"
    params = {"sn": serial_number}
    response = requests.get(url, headers=get_request_headers(), params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

def get_multiple_cases_status(serial_numbers, case_type="sn"):
    """
    Get status for multiple cases.

    Args:
        serial_numbers (list): List of serial numbers
        case_type (str): 'sn' for serial, 'rn' for registration

    Returns:
        dict: JSON response
    """
    ids = ",".join(serial_numbers)
    url = f"{BASE_URL}/ts/cd/caseMultiStatus/{case_type}"
    params = {"ids": ids}
    response = requests.get(url, headers=get_request_headers(), params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

def download_document(serial_number, doc_id, format_type="pdf"):
    """
    Download a document.

    Args:
        serial_number (str): Serial number
        doc_id (str): Document ID
        format_type (str): 'pdf' or 'zip'

    Returns:
        bytes: Document content
    """
    url = f"{BASE_URL}/ts/cd/casedoc/sn{serial_number}/{doc_id}/content.{format_type}"
    response = requests.get(url, headers=get_request_headers(accept=f"application/{format_type}"))

    if response.status_code == 200:
        return response.content
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

def main():
    # Example usage
    serial_number = "78787878"  # Example serial number

    print("Getting case status...")
    status = get_case_status(serial_number)
    if status:
        print(json.dumps(status, indent=2))

    print("\nGetting last update...")
    update = get_last_update(serial_number)
    if update:
        print(json.dumps(update, indent=2))

    # Uncomment to test multiple cases
    # print("\nGetting multiple cases...")
    # multiple = get_multiple_cases_status(["78787878", "76767676"])
    # if multiple:
    #     print(json.dumps(multiple, indent=2))

if __name__ == "__main__":
    main()