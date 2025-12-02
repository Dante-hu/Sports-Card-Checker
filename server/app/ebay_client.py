# app/ebay_client.py
import os
import requests
from typing import List, Dict, Any
import base64


# We’ll choose environment based on EBAY_ENVIRONMENT
def get_ebay_base_url() -> str:
    env = os.environ.get("EBAY_ENVIRONMENT", "PRODUCTION").upper()
    if env == "SANDBOX":
        return "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"
    # default: production
    return "https://api.ebay.com/buy/browse/v1/item_summary/search"


def get_ebay_token() -> str | None:
    """
    Uses the stored eBay REFRESH TOKEN to get a fresh ACCESS TOKEN.
    Returns the access token string, or None on failure.
    """

    client_id = os.getenv("EBAY_CLIENT_ID")
    client_secret = os.getenv("EBAY_CLIENT_SECRET")
    refresh_token = os.getenv("EBAY_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print(" Missing eBay environment variables.")
        return None

    # Prepare Basic Auth header
    basic_auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    url = "https://api.ebay.com/identity/v1/oauth2/token"

    headers = {
        "Authorization": f"Basic {basic_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": "https://api.ebay.com/oauth/api_scope",
    }

    resp = requests.post(url, headers=headers, data=data)

    if resp.status_code != 200:
        print("❌ Failed to refresh eBay token:", resp.text)
        return None

    token = resp.json().get("access_token")
    return token


def _call_ebay(q: str, limit: int, marketplace: str) -> List[Dict[str, Any]]:
    token = get_ebay_token()
    if not token:
        print("EBAY_OAUTH_TOKEN not set")
        return []

    url = get_ebay_base_url()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": marketplace,
    }

    params = {
        "q": q,
        "limit": str(limit),
    }

    print(f"[eBay] Searching {url} for: {q!r}")

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
    except Exception as exc:
        print("Error calling eBay API:", exc)
        return []

    if resp.status_code != 200:
        print(f"eBay API error {resp.status_code}: {resp.text[:300]}")
        return []

    data = resp.json()
    items = data.get("itemSummaries", [])
    if not isinstance(items, list):
        return []

    print(f"[eBay] Found {len(items)} items")
    return items


def search_ebay_items(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    marketplace = os.environ.get("EBAY_MARKETPLACE_ID", "EBAY_CA")  # or "EBAY_US"

    # Just one call for now (you can add fallback later)
    return _call_ebay(query, limit=limit, marketplace=marketplace)
