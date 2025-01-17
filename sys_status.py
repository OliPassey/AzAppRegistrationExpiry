import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.utils import formataddr
import smtplib
import logging

def check_client_id_expiry():
    # Load environment variables
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    tenant_id = os.getenv('AZURE_TENANT_ID')
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('FROM_EMAIL')
    from_name = os.getenv('FROM_NAME')
    admin_email = os.getenv('ADMIN_EMAIL')

    # Check if the client ID is expiring soon
    expiry_date_str = os.getenv('CLIENT_ID_EXPIRY_DATE')
    if not expiry_date_str:
        logging.error("CLIENT_ID_EXPIRY_DATE not set in environment variables")
        return

    try:
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
    except ValueError as e:
        logging.error(f"Error parsing CLIENT_ID_EXPIRY_DATE: {e}")
        return

    days_to_expiry = (expiry_date - datetime.utcnow()).days

    if days_to_expiry <= 30:
        subject = "Warning: Azure Client ID Expiry Notification"
        body = f"""
        <html>
        <body>
            <p>The Azure Client ID <strong>{client_id}</strong> is set to expire in 
            <span style="color: red; font-weight: bold;">{days_to_expiry} days</span> 
            on <strong>{expiry_date.strftime('%Y-%m-%d')}</strong>.</p>
            <p>Please take the necessary actions to renew the client ID before it expires.</p>
        </body>
        </html>
        """

        # Create email message
        msg = MIMEText(body, 'html')
        msg['Subject'] = subject
        msg['From'] = formataddr((from_name, from_email))
        msg['To'] = admin_email

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(from_email, admin_email, msg.as_string())
            logging.info(f"Successfully sent client ID expiry warning to {admin_email}")
        except Exception as e:
            logging.error(f"Failed to send client ID expiry warning: {e}")

if __name__ == "__main__":
    check_client_id_expiry()