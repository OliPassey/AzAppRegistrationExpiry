import os
import requests
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(asctime)s - %(message)s')

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

def list_drive_items(site_id, drive_id, parent_id=None):
    access_token = get_access_token()
    if not access_token:
        return None

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    if parent_id:
        items_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{parent_id}/children"
    else:
        items_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root/children"

    response = requests.get(items_url, headers=headers)
    if response.status_code != 200:
        logging.error(f"Failed to list drive items: {response.status_code}")
        logging.error(response.json())
        return None

    items = response.json().get('value', [])
    if not items:
        logging.error("No items found in the drive")
        return None

    for item in items:
        logging.info(f"Found item: {item.get('name')} with ID: {item.get('id')}")
        if item.get('folder'):
            # Recursively list items in the folder
            list_drive_items(site_id, drive_id, item.get('id'))

    return items

if __name__ == "__main__":
    site_id = "opassey.sharepoint.com,8e038e2a-139b-4e46-893a-bcf76062e063,5dcd71be-16b7-42ba-add6-4068b88ef3aa"
    drive_id = os.getenv('SHAREPOINT_DRIVE_ID')
    items = list_drive_items(site_id, drive_id)
    if items:
        logging.info("Listed drive items successfully")
    else:
        logging.error("Failed to list drive items")