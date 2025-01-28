# Azure Function App for Secret Expiry Notifications

This Azure Function App fetches Azure App Registrations, checks for expiring secrets, and sends email notifications to the owners.

## Prerequisites

- Azure Subscription
- Azure CLI
- Python 3.11
- Azure DevOps account
- Self-hosted agent (optional)

## Setup

### Local Development

1. **Clone the repository:**

   ```sh
   git clone https://github.com/OliPassey/AzAppRegistrationExpiry.git
   cd AzAppRegistrationExpiry
   ```

2. **Create local dev environment & Install dependencies**:
   Make sure you have Python3.11 installed, then run:
   ```
      python3.11 -m venv .venv
      source .venv/bin/activate
      pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   Create a local.settings.json file in the root of the function app directory with the following contents  
   {
     "IsEncrypted": false,
     "Values": {
       "AzureWebJobsStorage": "<YourAzureWebJobsStorage>",
       "FUNCTIONS_WORKER_RUNTIME": "python",
       "AZURE_CLIENT_ID": "<YourAzureClientId>",
       "AZURE_CLIENT_SECRET": "<YourAzureClientSecret>",
       "AZURE_TENANT_ID": "<YourAzureTenantId>",
       "SMTP_SERVER": "<YourSmtpServer>",
       "SMTP_PORT": "<YourSmtpPort>",
       "SMTP_USERNAME": "<YourSmtpUsername>",
       "SMTP_PASSWORD": "<YourSmtpPassword>",
       "FROM_EMAIL": "<YourFromEmail>",
       "FROM_NAME": "<YourFromName>",
       "TO_EMAIL": "<YourToEmail>"
     }
   }

4. **Run the function locally**:
   Use the Azure Functions Core Tools to run the function:
   ```
   func start
   ```

## Usage

Once the function is running, you can trigger it by sending an HTTP request to the endpoint provided in the console output. The function will authenticate to the Microsoft Graph API and return the app registrations.

## License

This project is licensed under the MIT License.
