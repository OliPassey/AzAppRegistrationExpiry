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
    logging.info("Processing a request to fetch app registrations.")

    app_registrations = get_app_registrations()
    if app_registrations:
        sorted_app_registrations = sort_app_registrations(app_registrations)
        send_notifications(sorted_app_registrations)

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

def sort_app_registrations(app_registrations):
    current_date = datetime.now(timezone.utc)
    for app in app_registrations:
        for credential in app["passwordCredentials"]:
            expiry_date_str = credential["endDateTime"]
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

def generate_html(app_registrations):
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    html = f"""
    <html>
    <head>
        <title>App Registrations</title>
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
        </style>
    </head>
    <body>
        <div class="intro">
            <h2>Azure App Registration Expiry Notification</h2>
            <p>This is an automated notification regarding expiring Azure App Registrations that you own or manage.</p>
            
            <p><strong>Why am I receiving this?</strong><br>
            You are receiving this email because you are listed as an owner of one or more Azure App Registrations that are approaching their expiration date or have already expired.</p>
            
            <p><strong>Required Actions:</strong></p>
            <ul>
                <li>Review the list of app registrations below</li>
                <li>For any expiring or expired registrations:
                    <ul>
                        <li>Verify if the app registration is still needed</li>
                        <li>If needed, renew the credentials before they expire</li>
                        <li>If not needed, consider removing the app registration</li>
                    </ul>
                </li>
            </ul>
            
            <p><strong>Color Coding:</strong></p>
            <ul>
                <li style="background-color: #d4edda; padding: 3px;">Green: More than 30 days until expiry</li>
                <li style="background-color: #fff3cd; padding: 3px;">Yellow: Between 8-30 days until expiry</li>
                <li style="background-color: #ffeeba; padding: 3px;">Orange: 7 days or less until expiry</li>
                <li style="background-color: #f8d7da; padding: 3px;">Red: Expired</li>
            </ul>

            <p>If you need assistance, please contact the IT Support team.</p>
        </div>

        <h1>App Registrations</h1>
        <p>Exported on: {current_time}</p>
        <table>
            <tr>
                <th>Display Name</th>
                <th>Expiry Date</th>
                <th>Days to Expiry</th>
                <th>Owners</th>
            </tr>
    """
    
    for app in app_registrations:
        owners = app.get('owners', [])
        owner_upns = [owner.get('userPrincipalName') for owner in owners if owner.get('userPrincipalName')]
        owner_list = ', '.join(owner_upns) if owner_upns else 'No owners'

        for credential in app.get('passwordCredentials', []):
            expiry_date = credential.get('expiry_date')
            days_to_expiry = credential.get('days_to_expiry')

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
                <td>{expiry_date.split('T')[0]}</td>
                <td>{days_to_expiry}</td>
                <td>{owner_list}</td>
            </tr>
            """
    
    html += """
        </table>
    </body>
    </html>
    """
    
    return html

def send_notifications(app_registrations):
    # Email credentials from environment variables
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('FROM_EMAIL')
    from_name = os.getenv('FROM_NAME')
    to_email = os.getenv('TO_EMAIL')

    # Generate HTML content
    html_content = generate_html(app_registrations)

    # Collect unique owner email addresses
    unique_owner_emails = set()
    for app in app_registrations:
        owners = app.get('owners', [])
        for owner in owners:
            email = owner.get('userPrincipalName')
            if email:
                unique_owner_emails.add(email)

    # Create email message
    subject = "App Registration Expiry Notification"
    msg = MIMEText(html_content, 'html')
    msg['Subject'] = subject
    msg['From'] = formataddr((from_name, from_email))
    msg['To'] = to_email
    msg['Cc'] = ', '.join(unique_owner_emails)

    try:
        logging.info(f"Sending email to {to_email} with CC to {', '.join(unique_owner_emails)}")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(from_email, [to_email] + list(unique_owner_emails), msg.as_string())
        logging.info("Successfully sent email")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")