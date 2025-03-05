# Azure App Registrations and Entra ID Account Expiry Notification
    
This repository contains an Azure Function that monitors Azure App Registrations and Entra ID account credentials, particularly focusing on the expiry of password credentials for both. It automatically fetches app registrations and account details, processes expiry information, and sends notifications to relevant stakeholders.
    
## Features
    
    - Fetches Azure App Registrations and associated credentials (password credentials).
    - Retrieves specific Entra ID accounts and checks their password expiration.
    - Sorts and classifies the credentials based on their expiry dates.
    - Sends a customized email notification to users, with an HTML table showing the details of expiring or expired credentials.
      
 ## Requirements
    
**Environment Variables**:  
The following environment variables are required for the function to authenticate to Microsoft Graph API and send emails.  
They will be set by the pipeline, an AzureDevOps Variable Group called "FunctionVariables" must be created manually. 
      - `AZURE_CLIENT_ID`: The Azure AD application client ID.  
      - `AZURE_CLIENT_SECRET`: The Azure AD application client secret.  
      - `AZURE_TENANT_ID`: The Azure AD tenant ID.  
      - `MONITORED_ACCOUNTS`: A comma-separated list of user principal names (UPNs) to monitor for password expiry.  
      - `SMTP_SERVER`: The SMTP server for sending email notifications.  
      - `SMTP_PORT`: The port to use for SMTP (usually 587).  
      - `SMTP_USERNAME`: The SMTP server username.  
      - `SMTP_PASSWORD`: The SMTP server password.  
      - `FROM_EMAIL`: The email address from which the notifications will be sent.  
      - `FROM_NAME`: The name displayed for the `FROM_EMAIL` address.  
      - `TO_EMAIL`: The recipient email address for the notifications.  
    
# Function Workflow
-----------------

1.  **Authentication**: The function authenticates to Microsoft Graph API using the Azure AD application credentials (Client ID, Client Secret, Tenant ID).
2.  **Fetching Data**:
    *   The function fetches all app registrations and their associated password credentials using Microsoft Graph API.
    *   It fetches user account details for the specified Entra ID accounts and checks for password expiration.
3.  **Processing Expiry Dates**: The credentials are processed to calculate the days until expiration. The credentials are sorted and categorized as:
    *   **Green**: More than 30 days to expiration.
    *   **Yellow**: Between 8-30 days to expiration.
    *   **Orange**: 7 days or less to expiration.
    *   **Red**: Expired.
    *   **Blue**: No expiration set.
4.  **Email Notification**:
    *   The function generates an HTML report that contains all relevant app registrations and account details.
    *   The report is sent via email to the specified recipient and optionally to the owners of the apps.

# Email Notification Example
--------------------------

The email notification contains an HTML table that shows:
*   **App Registrations**: Display name, secret name, expiry date, days to expiry, and owners.
*   **Entra ID Accounts**: Display name, user principal name, password expiry date, and status.

### Color Coding in the Notification:

*   **Green**: More than 30 days until expiry.
*   **Yellow**: Between 8-30 days until expiry.
*   **Orange**: 7 days or less until expiry.
*   **Red**: Expired.
*   **Blue**: No expiration set.

Notes
-----

*   Ensure that the monitored accounts list is correctly populated with the UPNs of the users whose password expiry you want to track.
*   The email notification will only be sent if there are app registrations or Entra ID accounts with upcoming or expired credentials.

 ## Local Setup
    
 ### 1. Clone the repository:
 ```bash
    git clone https://github.com/OliPassey/AzAppRegistrationExpiry.git
```    

### 2. Install dependencies:

Ensure that you have the necessary libraries installed in your environment:

```bash
    pip install -r requirements.txt
```

### 3. Configure Environment Variables:

You need to set the following environment variables:
*   **Azure Authentication**: These variables are used to authenticate against Microsoft Graph API.
*   **SMTP Configuration**: These variables are used to send email notifications.
Example for local development (Linux/macOS):
```bash
    export AZURE_CLIENT_ID="<your-client-id>"
    export AZURE_CLIENT_SECRET="<your-client-secret>"
    export AZURE_TENANT_ID="<your-tenant-id>"
    export MONITORED_ACCOUNTS="user1@domain.com, user2@domain.com"
    export SMTP_SERVER="smtp.yourserver.com"
    export SMTP_PORT="587"
    export SMTP_USERNAME="your-smtp-username"
    export SMTP_PASSWORD="your-smtp-password"
    export FROM_EMAIL="your-email@domain.com"
    export FROM_NAME="Your Name"
    export TO_EMAIL="recipient-email@domain.com"
 ```
or create a local.settings.json file:
```bash
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "<connection-string>",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_CLIENT_ID": "",
    "AZURE_CLIENT_SECRET": "",
    "AZURE_TENANT_ID": "",
    "SMTP_SERVER": "",
    "SMTP_PORT": "",
    "SMTP_USERNAME": "",
    "SMTP_PASSWORD": "",
    "FROM_EMAIL": "",
    "FROM_NAME": "",
    "TO_EMAIL": "",
    "MONITORED_ACCOUNTS": ""
  }
}
```
### 4a. Run Locally:
----------------------------

# Install Required tools:

1.  **Python 3.11**
    *   Download from [python.org](vscode-file://vscode-app/c:/Program%20Files/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-sandbox/workbench/workbench.html)
    *   Ensure it's added to your PATH
2.  **Azure Functions Core Tools v4**
    *   Install via npm: `npm install -g azure-functions-core-tools@4`
    *   Or download from [GitHub releases](vscode-file://vscode-app/c:/Program%20Files/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-sandbox/workbench/workbench.html)
3.  **Azure CLI**
    *   Download from [Microsoft's website](vscode-file://vscode-app/c:/Program%20Files/Microsoft%20VS%20Code/resources/app/out/vs/code/electron-sandbox/workbench/workbench.html)
    *   Needed for authenticating with Azure services

# Setup local environment

1.  **Create a Python Virtual Environment**
    
    ## Navigate to your project directory
    
    ```bash cd C:/code/AzAppRegistrationExpiry ```
    
    ## Create a virtual environment
    
    ```bash python -m venv .venv ``` 
    
    ## Activate the environment
    
    ## On Windows:
    
    ```bash     .venv\Scripts\activate ```
    
    ## On macOS/Linux:
    
    ```bash  source .venv/bin/activate ```
    
2.  **Install Dependencies**
    
    ```bash pip install -r requirements.txt ```
    
3.  **Setup local.settings.json**
    *   You already have this file with your settings configured
    *   Make sure it's in your project root directory

# Running the Function Locally


1.  **Start the Function App**
    
  ```bash 
     func start 
```
    
2.  **Trigger the Function Manually** (since it's a timer trigger)
      
    ```bash func function invoke aio --no-interactive ```

### 4. Deploy to Azure:
----------------------------

Follow [Azure Functions deployment guide](https://docs.microsoft.com/en-us/azure/azure-functions/functions-deploy) to deploy the function to Azure.
Also see additional Wiki document "Pipelines & Deployment"
```bash
func azure functionapp publish AzureAppRegExpMon --python
```

