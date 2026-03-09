"""
integrations/shopify.py - Shopify product listing, deletion, and order webhooks
"""

import requests
from config import SHOPIFY_STORE_URL, SHOPIFY_ACCESS_TOKEN, AGENT_TAG

BASE = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-01"
HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
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
        r = requests.post(f"{BASE}/products.json", json=payload, headers=HEADERS, timeout=20)
        r.raise_for_status()
        shopify_id = str(r.json().get("product", {}).get("id", ""))
        print(f"[Shopify] ✅ Listed: '{product['title']}' | ID: {shopify_id}")
        return shopify_id
    except Exception as e:
        print(f"[Shopify] ❌ Failed: {e}")
        return None


def delete_product(shopify_product_id: str) -> bool:
    """Delete a product from Shopify by ID."""
    try:
        r = requests.delete(f"{BASE}/products/{shopify_product_id}.json", headers=HEADERS, timeout=15)
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
        r = requests.post(f"{BASE}/webhooks.json", json=payload, headers=HEADERS, timeout=15)
        if r.status_code in [200, 201]:
            print(f"[Shopify] ✅ Order webhook registered: {server_url}/webhook/order")
            return True
        else:
            print(f"[Shopify] Webhook registration response: {r.status_code} {r.text}")
            return False
    except Exception as e:
        print(f"[Shopify] Webhook error: {e}")
        return False
