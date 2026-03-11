"""
integrations/shopify.py - Shopify integration with auto token refresh
Tokens expire every 24 hours, so we fetch a fresh one before each use.
"""

import requests
from config import (
    SHOPIFY_STORE_URL, SHOPIFY_CLIENT_ID,
    SHOPIFY_CLIENT_SECRET, AGENT_TAG
)

BASE = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-01"


def get_fresh_token() -> str:
    """Get a fresh access token using client credentials. Valid for 24 hours."""
    url = f"https://{SHOPIFY_STORE_URL}/admin/oauth/access_token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": SHOPIFY_CLIENT_ID,
        "client_secret": SHOPIFY_CLIENT_SECRET
    }
    try:
        r = requests.post(
            url,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )
        r.raise_for_status()
        token = r.json().get("access_token", "")
        print(f"[Shopify] ✅ Fresh token obtained")
        return token
    except Exception as e:
        print(f"[Shopify] ❌ Failed to get token: {e}")
        return ""


def get_headers() -> dict:
    """Get headers with a fresh token."""
    token = get_fresh_token()
    if not token:
        raise Exception("Could not get Shopify access token.")
    return {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json"
    }


def list_product(product: dict) -> str:
    """Create a draft product on Shopify. Returns Shopify product ID or None."""
    tags = list(product.get("tags", []))
    if AGENT_TAG not in tags:
        tags.append(AGENT_TAG)

    images = [{"src": url} for url in product.get("images", []) if url]

    payload = {
        "product": {
            "title": product["title"],
            "body_html": product.get("description", ""),
            "vendor": product.get("supplier", ""),
            "product_type": "Home Decor",
            "tags": ", ".join(tags),
            "status": "draft",
            "variants": [{
                "price": str(product.get("suggested_price", 999)),
                "inventory_management": None,
                "fulfillment_service": "manual"
            }],
            "images": images
        }
    }

    try:
        r = requests.post(
            f"{BASE}/products.json",
            json=payload,
            headers=get_headers(),
            timeout=20
        )
        r.raise_for_status()
        shopify_id = str(r.json().get("product", {}).get("id", ""))
        print(f"[Shopify] ✅ Listed: '{product['title']}' | ID: {shopify_id}")
        return shopify_id
    except Exception as e:
        print(f"[Shopify] ❌ Failed to list product: {e}")
        return None


def delete_product(shopify_product_id: str) -> bool:
    """Delete a product from Shopify by ID."""
    try:
        r = requests.delete(
            f"{BASE}/products/{shopify_product_id}.json",
            headers=get_headers(),
            timeout=15
        )
        return r.status_code == 200
    except Exception as e:
        print(f"[Shopify] Delete error: {e}")
        return False


def get_product_url(shopify_product_id: str) -> str:
    return f"https://{SHOPIFY_STORE_URL}/admin/products/{shopify_product_id}"


def register_order_webhook(server_url: str) -> bool:
    """Register a Shopify webhook to receive new order notifications."""
    payload = {
        "webhook": {
            "topic": "orders/create",
            "address": f"{server_url}/webhook/order",
            "format": "json"
        }
    }
    try:
        r = requests.post(
            f"{BASE}/webhooks.json",
            json=payload,
            headers=get_headers(),
            timeout=15
        )
        if r.status_code in [200, 201]:
            print(f"[Shopify] ✅ Webhook registered: {server_url}/webhook/order")
            return True
        print(f"[Shopify] Webhook response: {r.status_code} {r.text}")
        return False
    except Exception as e:
        print(f"[Shopify] Webhook error: {e}")
        return False
