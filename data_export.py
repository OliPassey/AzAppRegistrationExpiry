import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def write_to_json(app_registrations, filename='app_registrations.json'):
    """
    Write app registration data to a JSON file.
    
    :param app_registrations: List of app registration data
    :param filename: Name of the JSON file to write to
    """
    try:
        with open(filename, 'w') as f:
            json.dump(app_registrations, f, indent=4)
        logging.info(f"App registration data successfully written to {filename}")
    except Exception as e:
        logging.error(f"Failed to write app registration data to {filename}: {e}")

def generate_html(app_registrations):
    """
    Generate an HTML representation of the app registration data.
    
    :param app_registrations: List of app registration data
    :return: HTML string
    """
    current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    html = f"""
    <html>
    <head>
        <title>App Registrations</title>
        <style>
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
        password_credentials = app.get('passwordCredentials', [])
        if not password_credentials:
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
            days_to_expiry = (expiry_date - datetime.utcnow()).days
            
            # Determine row color class
            if days_to_expiry > 30:
                color_class = "green"
            elif 7 < days_to_expiry <= 30:
                color_class = "yellow"
            elif 1 <= days_to_expiry <= 7:
                color_class = "orange"
            else:
                color_class = "red"
                days_to_expiry = "EXPIRED"

            # Get owner information
            owners = app.get('owners', [])
            owner_upns = [owner.get('userPrincipalName') for owner in owners if owner.get('userPrincipalName')]
            owner_list = ', '.join(owner_upns) if owner_upns else 'No owners'

            html += f"""
            <tr class="{color_class}">
                <td>{app['displayName']}</td>
                <td>{expiry_date.strftime('%Y-%m-%d')}</td>
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

# Example usage
if __name__ == "__main__":
    # Sample app registration data
    app_registrations = [
        {
            "displayName": "App1",
            "passwordCredentials": [{"endDateTime": "2024-12-31T23:59:59.9999999Z"}]
        },
        {
            "displayName": "App2",
            "passwordCredentials": [{"endDateTime": "2025-01-15T23:59:59.9999999Z"}]
        }
    ]
    
    # Write to JSON
    write_to_json(app_registrations)
    
    # Generate HTML
    html_content = generate_html(app_registrations)
    with open('app_registrations.html', 'w') as f:
        f.write(html_content)
    logging.info("HTML content successfully written to app_registrations.html")