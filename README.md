# AzAppRegistrationExpiry

A simple python app to warn of upcoming App Registration Secret / Password Expiry on Azure Entra ID.

## Installation

Requires Python 3.12  
Install requirements from requirements.txt

```bash
pip install -r requirements.txt
```

## Usage

Amend the credentials in .env to match your environment.  
You will need to create an App Registration with API Permissions:  
- Application.ReadWrite.All  
- Files.ReadWrite.All
- Sites.ReadWrite.All
- User.Read
- User.Read.All  

Create an Excel Sheet within Business OneDrive and add the ID to the .env file  (sourcedoc=xxx in the URL)  
Add SMTP Sending details to .env (AWS Simple E-Mail Service was used in development)  


```python
python main.py
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.
