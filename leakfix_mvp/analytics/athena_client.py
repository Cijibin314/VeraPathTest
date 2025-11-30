import requests
from urllib.parse import urlencode
import os
import logging
from django.core.cache import cache

# Configure basic logging to print to the console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# These values are now read from environment variables for security.
# Populate them in your .env file.
CLIENT_ID = os.environ.get("ATHENA_CLIENT_ID", "your_client_id")
CLIENT_SECRET = os.environ.get("ATHENA_CLIENT_SECRET", "your_client_secret")
#TOKEN_URL = "https://api.preview.platform.athenahealth.com/oauth2/token"
TOKEN_URL = "https://api.preview.platform.athenahealth.com/oauth2/v1/token" 
def get_token():
    """
    Obtain an OAuth 2.0 token using client credentials.
    The token is cached to prevent hitting rate limits.
    """
    cache_key = 'athena_api_token'
    cached_token = cache.get(cache_key)
    if cached_token:
         logging.info("Using cached Athena API token.")
         return cached_token
 
    logging.info("Attempting to get new Athena API token...")
    try:
        data = {
             "grant_type": "client_credentials",
             "client_id": CLIENT_ID,
             "client_secret": CLIENT_SECRET,
             "scope": "athena/service/Athenanet.MDP.*"
         }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(TOKEN_URL, data=urlencode(data), headers=headers)
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 3600) # Default to 1 hour if not provided
 
        if access_token:
             # Cache the token for slightly less than its expiry to be safe
             cache.set(cache_key, access_token, expires_in - 300) # Cache for expires_in - 5 minutes
             logging.info("Successfully obtained and cached new Athena API token.")
             return access_token
        else:
             logging.error("Error: Access token not found in response.")
             return None
    except requests.exceptions.RequestException as e:
         logging.error(f"Error getting token: {e}")
         if e.response:
             logging.error(f"Response Body: {e.response.text}")
         return None

def get(endpoint, practice_id, token, params=None):
    """
    Perform a GET request against the Athenahealth API.
    """
    base_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}" 
    url = f"{base_url}/{endpoint.lstrip('/')}"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Log the full request URL
    full_url = requests.Request('GET', url, params=params or {}).prepare().url
    logging.info(f"Athena API Request: GET {full_url}")

    response = requests.get(full_url, headers=headers) # Use full_url here
    
    # Log the response status code
    logging.info(f"Athena API Response Status: {response.status_code}")

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Athena API Error Response Body: {e.response.text}")
        raise # Re-raise the exception after logging
        
    return response.json()
