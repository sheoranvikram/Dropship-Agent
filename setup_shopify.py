"""
setup_shopify.py - One-time Shopify OAuth setup
Run this once to get your permanent access token.

Steps:
1. Run: python setup_shopify.py
2. Copy the URL it gives you
3. Open that URL in your browser
4. Approve the app on your Shopify store
5. You'll be redirected — copy the 'code' from the URL
6. Paste it back here when asked
7. Copy the access token and add it to Railway Variables as SHOPIFY_ACCESS_TOKEN
"""

import requests
import urllib.parse
from config import SHOPIFY_STORE_URL, SHOPIFY_CLIENT_ID, SHOPIFY_CLIENT_SECRET, SERVER_BASE_URL

SCOPES = "read_products,write_products,read_orders"
REDIRECT_URI = f"{SERVER_BASE_URL}/shopify/callback"


def get_auth_url() -> str:
    params = {
        "client_id": SHOPIFY_CLIENT_ID,
        "scope": SCOPES,
        "redirect_uri": REDIRECT_URI,
        "state": "dropshipagent"
    }
    query = urllib.parse.urlencode(params)
    return f"https://{SHOPIFY_STORE_URL}/admin/oauth/authorize?{query}"


def exchange_code_for_token(code: str) -> str:
    url = f"https://{SHOPIFY_STORE_URL}/admin/oauth/access_token"
    payload = {
        "client_id": SHOPIFY_CLIENT_ID,
        "client_secret": SHOPIFY_CLIENT_SECRET,
        "code": code
    }
    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()
    return r.json().get("access_token", "")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  SHOPIFY OAUTH SETUP")
    print("="*60)
    print("\nStep 1: Open this URL in your browser:\n")
    print(get_auth_url())
    print("\nStep 2: Click 'Install app' on your Shopify store")
    print("Step 3: After approval, you'll be redirected to a URL")
    print("        The URL will look like:")
    print(f"        {SERVER_BASE_URL}/shopify/callback?code=XXXXXX&...")
    print("\nStep 4: Copy the 'code' value from that URL")

    code = input("\nPaste the code here: ").strip()

    if not code:
        print("❌ No code entered. Exiting.")
        exit(1)

    print("\nExchanging code for access token...")
    try:
        token = exchange_code_for_token(code)
        if token:
            print("\n" + "="*60)
            print("✅ SUCCESS! Your Shopify Access Token:")
            print("="*60)
            print(f"\n{token}\n")
            print("="*60)
            print("\nNow add this to Railway Variables as:")
            print("  Key:   SHOPIFY_ACCESS_TOKEN")
            print(f"  Value: {token}")
            print("\nThen redeploy your Railway project.")
            print("="*60 + "\n")
        else:
            print("❌ Failed to get token. Check your Client ID and Secret.")
    except Exception as e:
        print(f"❌ Error: {e}")
