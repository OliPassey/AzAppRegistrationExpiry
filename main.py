from azure_client import get_app_registrations
from sharepoint_client import store_app_registrations  # Uncomment this line
from notification import send_notifications
from data_export import write_to_json, generate_html

def main():
    app_registrations = get_app_registrations()
    store_app_registrations(app_registrations)
    write_to_json(app_registrations)
    html_content = generate_html(app_registrations)
    with open('app_registrations.html', 'w') as f:
        f.write(html_content)
    send_notifications(app_registrations)

if __name__ == "__main__":
    main()