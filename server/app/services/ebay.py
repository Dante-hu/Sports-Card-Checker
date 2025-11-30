import os
import base64
import requests

def get_ebay_access_token():
    client_id = os.getenv("EBAY_CLIENT_ID")
    client_secret = os.getenv("EBAY_CLIENT_SECRET")
    refresh_token = os.getenv("EBAY_REFRESH_TOKEN")

    basic_auth = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()

    url = "https://api.ebay.com/identity/v1/oauth2/token"

    headers = {
        "Authorization": f"Basic {basic_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": "https://api.ebay.com/oauth/api_scope"
    }

    response = requests.post(url, headers=headers, data=data)
    return response.json()
