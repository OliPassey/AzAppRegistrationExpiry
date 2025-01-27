# Azure Function App

This project is an Azure Function that authenticates to the Microsoft Graph API and fetches app registrations. The function is triggered by an HTTP request.

## Project Structure

```
azure-function-app
├── aio
│   ├── __init__.py       # Contains the main logic for the Azure Function
│   └── function.json     # Configuration for the Azure Function
├── local.settings.json    # Local configuration settings
├── requirements.txt       # Required Python packages
└── README.md              # Project documentation
```

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd azure-function-app
   ```

2. **Install dependencies**:
   Make sure you have Python installed, then run:
   ```
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   Create a `.env` file or set the following environment variables in `local.settings.json`:
   - `AZURE_CLIENT_ID`: Your Azure AD application client ID
   - `AZURE_CLIENT_SECRET`: Your Azure AD application client secret
   - `AZURE_TENANT_ID`: Your Azure AD tenant ID

4. **Run the function locally**:
   Use the Azure Functions Core Tools to run the function:
   ```
   func start
   ```

## Usage

Once the function is running, you can trigger it by sending an HTTP request to the endpoint provided in the console output. The function will authenticate to the Microsoft Graph API and return the app registrations.

## License

This project is licensed under the MIT License.