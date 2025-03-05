import os
import logging
import json
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime, timezone
import requests
import msal
import azure.functions as func

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main(myTimer: func.TimerRequest) -> None:
    logging.info("Processing a request to fetch app registrations and other credentials.")

    app_registrations = get_app_registrations()
    entra_id_accounts = get_entra_id_accounts_password_expiry()

    if app_registrations or entra_id_accounts:
        sorted_app_registrations = sort_app_registrations(app_registrations)
        send_notifications(sorted_app_registrations, entra_id_accounts)

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
        
        app_registrations = response.json().get('value', [])
        logging.info(f"Fetched {len(app_registrations)} app registrations")
        return app_registrations

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching app registrations: {e}")
        return []

def get_entra_id_accounts_password_expiry():
    logging.info("Fetching Entra ID accounts password expiry")

    # Azure AD app credentials from environment variables
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    tenant_id = os.getenv('AZURE_TENANT_ID')
    
    # Get the list of specific accounts to monitor
    # Format should be comma-separated UPNs (user principal names)
    accounts_to_monitor = os.getenv('MONITORED_ACCOUNTS', '')
    accounts_list = [account.strip() for account in accounts_to_monitor.split(',') if account.strip()]
    
    if not accounts_list:
        logging.warning("No specific Entra ID accounts configured for monitoring")
        return []
    
    logging.info(f"Configured to monitor {len(accounts_list)} specific Entra ID accounts")

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

    # Create headers for the request
    headers = {
        "Authorization": f"Bearer {access_token}",
        "ConsistencyLevel": "eventual"
    }
    
    # Collect account information for each user
    entra_id_accounts = []
    
    for upn in accounts_list:
        try:
            # Use the user's UPN to query specific user details - now including mail field
            graph_url = f"https://graph.microsoft.com/v1.0/users/{upn}?$select=id,displayName,userPrincipalName,mail,passwordPolicies,passwordProfile"
            
            logging.info(f"Fetching details for account: {upn}")
            response = requests.get(graph_url, headers=headers)
            
            if response.status_code == 200:
                account = response.json()
                entra_id_accounts.append(account)
                logging.info(f"Successfully fetched details for account: {upn}")
            else:
                logging.warning(f"Failed to fetch details for account {upn}: {response.status_code} {response.reason}")
                logging.warning(f"Response: {response.text[:200]}...")
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching details for account {upn}: {e}")
    
    logging.info(f"Fetched {len(entra_id_accounts)} Entra ID accounts out of {len(accounts_list)} configured")
    return entra_id_accounts

def sort_app_registrations(app_registrations):
    current_date = datetime.now(timezone.utc)
    for app in app_registrations:
        for credential in app["passwordCredentials"]:
            expiry_date_str = credential["endDateTime"]
            
            # Include the credential display name or ID for identification
            credential_name = credential.get("displayName", "")
            if not credential_name:
                # Use the last 4 characters of the keyId as an identifier if no display name
                credential_name = f"Secret {credential.get('keyId', '')[-4:]}"
            
            credential["name"] = credential_name
            
            try:
                if '.' in expiry_date_str:
                    expiry_date_str = expiry_date_str.split('.')[0] + '.' + expiry_date_str.split('.')[1][:6] + 'Z'
                if expiry_date_str.endswith('ZZ'):
                    expiry_date_str = expiry_date_str[:-1]
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
            except ValueError:
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
            days_to_expiry = (expiry_date - current_date).days
            credential["days_to_expiry"] = days_to_expiry
            credential["expiry_date"] = expiry_date.isoformat()

    sorted_apps = sorted(app_registrations, key=lambda x: (min([cred["days_to_expiry"] for cred in x["passwordCredentials"]]) if x["passwordCredentials"] else float('inf')), reverse=False)
    return sorted_apps

def generate_html(app_registrations, entra_id_accounts):
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    html = f"""
    <html>
    <head>
        <title>App Registrations and Credentials</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                color: #333;
            }}
            .intro {{
                margin-bottom: 20px;
                line-height: 1.5;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                border: 1px solid black;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .green {{
                background-color: #d4edda;
            }}
            .yellow {{
                background-color: #fff3cd;
            }}
            .orange {{
                background-color: #ffeeba;
            }}
            .red {{
                background-color: #f8d7da;
            }}
            .blue {{
                background-color: #cce5ff;
            }}
        </style>
    </head>
    <body>
        <div class="intro">
            <h2>Azure App Registration and Credential Expiry Notification</h2>
            <p>This is an automated notification regarding expiring Azure App Registrations and Entra ID account passwords that you own or manage.</p>
            
            <p><strong>Why am I receiving this?</strong><br>
            You are receiving this email because you are listed as an owner of one or more Azure App Registrations or Entra ID accounts that are approaching their expiration date or have already expired.</p>
            
            <p><strong>Required Actions:</strong></p>
            <ul>
                <li>Review the list of app registrations and accounts below</li>
                <li>For any expiring or expired credentials:
                    <ul>
                        <li>Verify if the credential is still needed</li>
                        <li>If needed, renew the credentials before they expire</li>
                        <li>If not needed, consider removing the credential</li>
                    </ul>
                </li>
            </ul>
            
            <p><strong>Color Coding:</strong></p>
            <ul>
                <li style="background-color: #d4edda; padding: 3px;">Green: More than 30 days until expiry</li>
                <li style="background-color: #fff3cd; padding: 3px;">Yellow: Between 8-30 days until expiry</li>
                <li style="background-color: #ffeeba; padding: 3px;">Orange: 7 days or less until expiry</li>
                <li style="background-color: #f8d7da; padding: 3px;">Red: Expired</li>
                <li style="background-color: #cce5ff; padding: 3px;">Blue: No expiration set / Password never expires</li>
            </ul>

            <p>If you need assistance, please contact the IT Support team.</p>
        </div>

        <h1>App Registrations</h1>
        <p>Exported on: {current_time}</p>
        <table>
            <tr>
                <th>Display Name</th>
                <th>Secret Name</th>
                <th>Expiry Date</th>
                <th>Days to Expiry</th>
                <th>Owners</th>
            </tr>
    """
    
    # Process app registrations
    for app in app_registrations:
        owners = app.get('owners', [])
        owner_upns = [owner.get('userPrincipalName') for owner in owners if owner.get('userPrincipalName')]
        owner_list = ', '.join(owner_upns) if owner_upns else 'No owners'

        for credential in app.get('passwordCredentials', []):
            expiry_date = credential.get('expiry_date')
            days_to_expiry = credential.get('days_to_expiry')
            secret_name = credential.get('name', 'Secret')

            if days_to_expiry is not None:
                if days_to_expiry > 30:
                    color_class = "green"
                elif 7 < days_to_expiry <= 30:
                    color_class = "yellow"
                elif 1 <= days_to_expiry <= 7:
                    color_class = "orange"
                else:
                    color_class = "red"
                    days_to_expiry = "EXPIRED"
            else:
                color_class = "red"
                days_to_expiry = "EXPIRED"

            html += f"""
            <tr class="{color_class}">
                <td>{app['displayName']}</td>
                <td>{secret_name}</td>
                <td>{expiry_date.split('T')[0] if expiry_date else 'N/A'}</td>
                <td>{days_to_expiry}</td>
                <td>{owner_list}</td>
            </tr>
            """

    # Process Entra ID accounts section
    html += """
        </table>
        <h1>Entra ID Accounts</h1>
        <table>
            <tr>
                <th>Display Name</th>
                <th>User Principal Name</th>
                <th>Password Expiry Date</th>
                <th>Status</th>
            </tr>
    """
    
    # Check if entra_id_accounts is not empty and has items
    if entra_id_accounts and len(entra_id_accounts) > 0:
        for account in entra_id_accounts:
            try:
                # Safe access to display name and userPrincipalName
                display_name = account.get('displayName', 'Unknown')
                upn = account.get('userPrincipalName', 'Unknown')
                
                # Get the clean email - use mail property if available, otherwise use UPN
                email = account.get('mail') or upn
                
                # If it's a guest account with #EXT#, display a cleaner version
                if '#EXT#' in upn and not account.get('mail'):
                    # Extract the email portion before the #EXT# part
                    try:
                        # Format is typically: username_domain.com#EXT#@tenant.onmicrosoft.com
                        # We want to convert to: username@domain.com
                        parts = upn.split('#EXT#')[0]
                        if '_' in parts:
                            username, domain = parts.rsplit('_', 1)
                            email = f"{username}@{domain}"
                    except:
                        # If parsing fails, keep the original
                        email = upn
                
                # Check password policies to see if password never expires
                password_policies = account.get('passwordPolicies', '')
                if password_policies is None:
                    password_policies = ''
                password_never_expires = 'DisablePasswordExpiration' in password_policies
                
                # Safe access to passwordProfile and passwordExpirationDateTime
                password_profile = account.get('passwordProfile')
                password_expiry_date_str = None
                
                if password_profile and isinstance(password_profile, dict):
                    password_expiry_date_str = password_profile.get('passwordExpirationDateTime')
                
                if password_never_expires:
                    color_class = "blue"
                    expiry_date_display = "N/A"
                    status = "Password Never Expires"
                elif password_expiry_date_str:
                    password_expiry_date = datetime.strptime(password_expiry_date_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
                    expiry_date_display = password_expiry_date.strftime('%Y-%m-%d')
                    days_to_expiry = (password_expiry_date - datetime.now(timezone.utc)).days

                    if days_to_expiry > 30:
                        color_class = "green"
                        status = f"{days_to_expiry} days remaining"
                    elif 7 < days_to_expiry <= 30:
                        color_class = "yellow"
                        status = f"{days_to_expiry} days remaining"
                    elif 1 <= days_to_expiry <= 7:
                        color_class = "orange"
                        status = f"{days_to_expiry} days remaining"
                    else:
                        color_class = "red"
                        status = "EXPIRED"
                else:
                    color_class = "blue"
                    expiry_date_display = "N/A"
                    status = "No Expiration Set"

                html += f"""
                <tr class="{color_class}">
                    <td>{display_name}</td>
                    <td>{email}</td>
                    <td>{expiry_date_display}</td>
                    <td>{status}</td>
                </tr>
                """
            except Exception as e:
                # Log full exception details for better debugging
                logging.error(f"Error processing Entra ID account {account.get('userPrincipalName', 'Unknown')}: {e}")
                logging.error(f"Account data: {account}")
                
                # Add a row for the account with error information
                html += f"""
                <tr class="red">
                    <td>{account.get('displayName', 'Unknown')}</td>
                    <td>{account.get('userPrincipalName', 'Unknown')}</td>
                    <td>Error</td>
                    <td>Failed to process account information</td>
                </tr>
                """
    else:
        html += """
        <tr>
            <td colspan="4">No Entra ID accounts found or unable to access accounts</td>
        </tr>
        """
    
    html += """
        </table>
    </body>
    </html>
    """
    
    return html

def send_notifications(app_registrations, entra_id_accounts):
    # Email credentials from environment variables
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('FROM_EMAIL')
    from_name = os.getenv('FROM_NAME')
    to_email = os.getenv('TO_EMAIL')

    # Generate HTML content
    html_content = generate_html(app_registrations, entra_id_accounts)

    # Collect unique owner email addresses
    unique_owner_emails = set()
    for app in app_registrations:
        owners = app.get('owners', [])
        for owner in owners:
            email = owner.get('userPrincipalName')
            if email:
                # Clean up guest user email addresses
                if '#EXT#' in email:
                    try:
                        # Format is typically: username_domain.com#EXT#@tenant.onmicrosoft.com
                        # We want to convert to: username@domain.com
                        parts = email.split('#EXT#')[0]
                        if '_' in parts:
                            username, domain = parts.rsplit('_', 1)
                            email = f"{username}@{domain}"
                    except Exception as e:
                        logging.warning(f"Error cleaning up guest email {email}: {e}")
                
                unique_owner_emails.add(email)

    # Create email message
    subject = "App Registration and Credential Expiry Notification"
    msg = MIMEText(html_content, 'html')
    msg['Subject'] = subject
    msg['From'] = formataddr((from_name, from_email))
    msg['To'] = to_email
    
    # Only include CC if there are owner emails
    if unique_owner_emails:
        msg['Cc'] = ', '.join(unique_owner_emails)
        recipients = [to_email] + list(unique_owner_emails)
    else:
        recipients = [to_email]

    try:
        logging.info(f"Sending email to {to_email}" + (f" with CC to {', '.join(unique_owner_emails)}" if unique_owner_emails else ""))
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(from_email, recipients, msg.as_string())
        logging.info("Successfully sent email")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")