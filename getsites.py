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

def list_sites():
    access_token = get_access_token()
    if not access_token:
        return None

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    sites_url = "https://graph.microsoft.com/v1.0/sites?search=*"
    response = requests.get(sites_url, headers=headers)
    if response.status_code != 200:
        logging.error(f"Failed to list sites: {response.status_code}")
        logging.error(response.json())
        return None

    sites = response.json().get('value', [])
    if not sites:
        logging.error("No sites found")
        return None

    for site in sites:
        logging.info(f"Found site: {site.get('name')} with ID: {site.get('id')}")

    return sites

if __name__ == "__main__":
    sites = list_sites()
    if sites:
        logging.info("Listed sites successfully")
    else:
        logging.error("Failed to list sites")