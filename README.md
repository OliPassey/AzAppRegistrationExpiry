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

Once the function is running, it will run every week day morning at 9am and send an email with results. The TO_EMAIL should be the administrator email for EntraID or whoever looks after App Registrations. It will also CC: all App Owners as listed in the App Registration.  

## Deployment  

1. **Create an Azure DevOps Project (Private)** 
2. **Create a Variable Group in Azure DevOps:**

Go to Pipelines > Library.  

Click on + Variable group.  

Name your variable group (e.g., MyVariableGroup).  

Add the following variables and mark sensitive variables as secrets:

AzureWebJobsStorage  
AZURE_CLIENT_ID  
AZURE_CLIENT_SECRET  
AZURE_TENANT_ID  
SMTP_SERVER  
SMTP_PORT  
SMTP_USERNAME  
SMTP_PASSWORD  
FROM_EMAIL  
FROM_NAME  
TO_EMAIL  

3. **Create a Pipeline from the Azure-pipeline.yaml file in the root of the repo**
4. **Run the Pipeline:**

Trigger the pipeline to deploy the infrastructure and the function app code.
