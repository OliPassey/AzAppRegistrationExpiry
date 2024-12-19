import os
from dotenv import load_dotenv
import logging
import json
import msal
import requests

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_app_registrations():
    logging.info("Authenticating to Microsoft Graph API")

    # Azure AD app credentials from environment variables
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    tenant_id = os.getenv('AZURE_TENANT_ID')

    authority = f"https://login.microsoftonline.com/{tenant_id}"
    scope = ["https://graph.microsoft.com/.default"]

    # Create a confidential client application
    app = msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret
    )

    # Acquire a token
    result = app.acquire_token_for_client(scopes=scope)

    if "access_token" in result:
        logging.info("Successfully authenticated to Microsoft Graph API")
        access_token = result["access_token"]
    else:
        logging.error("Failed to authenticate to Microsoft Graph API")
        logging.error(result.get("error"))
        logging.error(result.get("error_description"))
        logging.error(result.get("correlation_id"))
        return []

    # Fetch app registrations with owners
    # Updated URL to include both app registration and owner data
    graph_url = (
        "https://graph.microsoft.com/v1.0/applications"
        "?$select=id,appId,displayName,passwordCredentials"
        "&$expand=owners($select=userPrincipalName)"
    )
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "ConsistencyLevel": "eventual"
    }

    try:
        response = requests.get(graph_url, headers=headers)
        response.raise_for_status()
        
        # Debug log the raw response
        #logging.info(f"API Response Status: {response.status_code}")
        #logging.debug(f"API Response: {response.text[:1000]}...")  # First 1000 chars
        
        app_registrations = response.json().get('value', [])
        logging.info(f"Fetched {len(app_registrations)} app registrations")
        return app_registrations

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching app registrations: {e}")
        return []

if __name__ == "__main__":
    app_registrations = get_app_registrations()
    # Write to JSON file for inspection
    with open('debug_app_registrations.json', 'w') as f:
        json.dump(app_registrations, f, indent=2)