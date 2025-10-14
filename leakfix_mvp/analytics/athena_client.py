import requests
from urllib.parse import urlencode
import os

# These values are now read from environment variables for security.
# Populate them in your .env file.
CLIENT_ID = os.environ.get("ATHENA_CLIENT_ID", "your_client_id")
CLIENT_SECRET = os.environ.get("ATHENA_CLIENT_SECRET", "your_client_secret")
#TOKEN_URL = "https://api.preview.platform.athenahealth.com/oauth2/token"
TOKEN_URL = "https://api.preview.platform.athenahealth.com/oauth2/v1/token" 
def get_token():
    """
    Obtain an OAuth 2.0 token using client_credentials (2‑legged OAuth).
    """
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "athena/service/Athenanet.MDP.*"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(TOKEN_URL, data=urlencode(data), headers=headers)
    response.raise_for_status()
    return response.json()["access_token"]

def get(endpoint, practice_id, token, params=None):
    """
    Perform a GET request against the Athenahealth API.
    """
    #base_url = f"https://api.platform.athenahealth.com/v1/{practice_id}"
    base_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}" 
    url = f"{base_url}/{endpoint.lstrip('/')}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, params=params or {})
    response.raise_for_status()
    return response.json()
