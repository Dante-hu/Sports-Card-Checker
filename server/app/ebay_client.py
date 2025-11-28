# app/ebay_client.py
import os
import requests

EBAY_BROWSE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"


def search_ebay_items(query: str, limit: int = 5):
    """Search eBay Browse API for a query string."""
    token = os.environ.get("EBAY_OAUTH_TOKEN")
    marketplace = os.environ.get("EBAY_MARKETPLACE_ID", "EBAY_US")

    if not token:
        raise RuntimeError("EBAY_OAUTH_TOKEN not set in .env")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": marketplace,
        "Content-Type": "application/json",
    }
    params = {
        "q": query,
        "limit": limit,
    }

    resp = requests.get(EBAY_BROWSE_URL, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()
