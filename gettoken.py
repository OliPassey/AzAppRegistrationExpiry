import os
import requests
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_access_token():
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    tenant_id = os.getenv('AZURE_TENANT_ID')

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default'
    }

    token_response = requests.post(token_url, data=token_data)
    access_token = token_response.json().get('access_token')
    if not access_token:
        logging.error("Failed to obtain access token")
        logging.error(token_response.json())
        return None

    return access_token

def get_drive_id(site_id):
    access_token = get_access_token()
    if not access_token:
        return None

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    response = requests.get(drives_url, headers=headers)
    if response.status_code != 200:
        logging.error(f"Failed to get drives: {response.status_code}")
        logging.error(response.json())
        return None

    drives = response.json().get('value', [])
    if not drives:
        logging.error("No drives found")
        return None

    # Assuming you want the first drive in the list
    drive_id = drives[0].get('id')
    logging.info(f"Found drive ID: {drive_id}")
    return drive_id

if __name__ == "__main__":
    site_id = os.getenv('SHAREPOINT_SITE_ID')
    drive_id = get_drive_id(site_id)
    if drive_id:
        logging.info(f"Drive ID: {drive_id}")
    else:
        logging.error("Failed to obtain drive ID")