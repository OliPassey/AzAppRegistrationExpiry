import os
from dotenv import load_dotenv
import requests
from datetime import datetime
import logging
import json

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

def update_excel_file(site_id, drive_id, file_id, data):
    """
    Update Excel Online file with new data using OneDrive for Business API
    """
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    tenant_id = os.getenv('AZURE_TENANT_ID')

    # Get access token
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
        return

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    try:
        # Get the file details to verify it exists
        file_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{file_id}"
        file_response = requests.get(file_url, headers=headers)
        file_response.raise_for_status()
        logging.info(f"Found file: {file_response.json().get('name')}")

        # Clear existing data (except header)
        clear_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{file_id}/workbook/worksheets/Sheet1/range(address='A2:D1000')"
        clear_data = {
            "values": [[""]*4]*999
        }
        response = requests.patch(clear_url, headers=headers, json=clear_data)
        response.raise_for_status()
        logging.info("Cleared existing data from Excel file")

        # Write new data
        update_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{file_id}/workbook/worksheets/Sheet1/range(address='A2:D{len(data)+1}')"
        update_data = {
            "values": data
        }
        response = requests.patch(update_url, headers=headers, json=update_data)
        response.raise_for_status()
        logging.info(f"Successfully wrote {len(data)} rows to Excel file")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error updating Excel file: {e}")
        if hasattr(e.response, 'text'):
            logging.error(f"Response content: {e.response.text}")
        raise

def store_app_registrations(app_registrations):
    # Get current date
    current_date = datetime.utcnow()

    # Prepare data for Excel
    excel_data = []
    for app in app_registrations:
        password_credentials = app.get('passwordCredentials', [])
        if not password_credentials:
            logging.warning(f"No password credentials found for {app['displayName']}")
            continue

        expiry_date = password_credentials[0].get('endDateTime')
        if expiry_date:
            if expiry_date.endswith('ZZ'):
                expiry_date = expiry_date[:-1]
            elif expiry_date.endswith('Z'):
                expiry_date = expiry_date[:-1]
            
            try:
                expiry_date_obj = datetime.strptime(expiry_date.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                days_to_expiry = (expiry_date_obj - current_date).days

                # Get owner information
                owners = app.get('owners', [])
                owner_upns = [owner.get('userPrincipalName') for owner in owners if owner.get('userPrincipalName')]
                owner_list = ', '.join(owner_upns) if owner_upns else 'No owners'

                excel_data.append([
                    app['displayName'],
                    expiry_date_obj.strftime('%Y-%m-%d'),
                    str(days_to_expiry),
                    owner_list
                ])

            except ValueError as e:
                logging.error(f"Error parsing expiry date for {app['displayName']}: {e}")
                continue

    # Update Excel file
    try:
        site_id = os.getenv('SHAREPOINT_SITE_ID')
        drive_id = os.getenv('SHAREPOINT_DRIVE_ID')
        file_id = os.getenv('EXCEL_FILE_ID')
        update_excel_file(site_id, drive_id, file_id, excel_data)
        logging.info("Successfully updated Excel file")
    except Exception as e:
        logging.error(f"Failed to update Excel file: {e}")

    logging.info("Finished processing app registrations")

if __name__ == "__main__":
    site_id = os.getenv('SHAREPOINT_SITE_ID')
    drive_id = get_drive_id(site_id)
    if drive_id:
        logging.info(f"Drive ID: {drive_id}")
    else:
        logging.error("Failed to obtain drive ID")