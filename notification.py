import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime
import requests
import json
import logging
from data_export import generate_html, generate_expiry_text

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_notifications(app_registrations):
    # Email credentials from environment variables
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('FROM_EMAIL')
    from_name = os.getenv('FROM_NAME')
    to_email = os.getenv('TO_EMAIL')

    # Teams webhook URL from environment variables
    teams_webhook_url = os.getenv('TEAMS_WEBHOOK_URL')

    # Get the current date
    current_date = datetime.utcnow()
    notification_periods = [60, 30, 7, 1]

    # Generate HTML content
    html_content = generate_html(app_registrations)

    # Send notification email and Teams message
    for app in app_registrations:
        # Debug log the entire app object
        #logging.info(f"Processing app: {json.dumps(app, indent=2)}")
        
        password_credentials = app.get('passwordCredentials', [])
        if not password_credentials:
            logging.warning(f"No password credentials found for {app['displayName']}")
            continue

        expiry_date = password_credentials[0].get('endDateTime')
        if expiry_date:
            # Clean up the date string
            if expiry_date.endswith('ZZ'):
                expiry_date = expiry_date[:-1]
            elif expiry_date.endswith('Z'):
                expiry_date = expiry_date[:-1]
            # Truncate the fractional seconds part to 6 digits if present
            if '.' in expiry_date:
                expiry_date = expiry_date.split('.')[0] + '.' + expiry_date.split('.')[1][:6] + 'Z'
            else:
                expiry_date += '.000000Z'
            try:
                expiry_date = datetime.strptime(expiry_date, '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError as e:
                logging.error(f"Error parsing expiry date for {app['displayName']}: {e}")
                continue
            days_to_expiry = (expiry_date - current_date).days
            if days_to_expiry in notification_periods or days_to_expiry < 0:
                subject = f"App Registration Expiry Notification: {app['displayName']}"
                body = generate_expiry_text(app['displayName'], days_to_expiry, expiry_date) + html_content

                # Fetch and debug log owner information
                owners = app.get('owners', [])
                #logging.info(f"Found owners for {app['displayName']}: {json.dumps(owners, indent=2)}")

                # Get CC emails from owners
                cc_emails = []
                for owner in owners:
                    email = owner.get('userPrincipalName') or owner.get('mail')
                    if email:
                        cc_emails.append(email)
                        logging.info(f"Added owner email for {app['displayName']}: {email}")

                # Create email message
                msg = MIMEText(body, 'html')
                msg['Subject'] = subject
                msg['From'] = formataddr((from_name, from_email))
                msg['To'] = to_email

                # Add CC recipients if any found
                if cc_emails:
                    msg['Cc'] = ', '.join(cc_emails)
                    logging.info(f"Added CC recipients for {app['displayName']}: {cc_emails}")

                try:
                    # Include CC recipients in sendmail
                    all_recipients = [to_email] + cc_emails
                    logging.info(f"Sending email for {app['displayName']} to all recipients: {all_recipients}")
                    
                    with smtplib.SMTP(smtp_server, smtp_port) as server:
                        server.starttls()
                        server.login(smtp_username, smtp_password)
                        server.sendmail(from_email, all_recipients, msg.as_string())
                    logging.info(f"Successfully sent email for {app['displayName']}")
                except Exception as e:
                    logging.error(f"Failed to send email for {app['displayName']}: {e}")

                # Send Teams notification
                teams_message = {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "summary": subject,
                    "themeColor": "0076D7",
                    "title": subject,
                    "sections": [{
                        "activityTitle": f"App Registration Expiry Notification",
                        "text": body
                    }]
                }

                try:
                    response = requests.post(teams_webhook_url, headers={"Content-Type": "application/json"}, json=teams_message)
                    response.raise_for_status()
                    logging.info(f"Teams notification sent for {app['displayName']}")
                except requests.exceptions.RequestException as e:
                    logging.error(f"Failed to send Teams notification for {app['displayName']}: {e}")

if __name__ == "__main__":
    # Sample app registration data for testing
    app_registrations = [
        {
            "displayName": "App1",
            "passwordCredentials": [{"endDateTime": "2024-12-31T23:59:59.9999999Z"}],
            "owners": [{"userPrincipalName": "owner1@example.com"}]
        },
        {
            "displayName": "App2",
            "passwordCredentials": [{"endDateTime": "2025-01-15T23:59:59.9999999Z"}],
            "owners": [{"userPrincipalName": "owner2@example.com"}]
        }
    ]
    
    # Send notifications
    send_notifications(app_registrations)