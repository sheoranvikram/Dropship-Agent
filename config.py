# ============================================================
# DROPSHIP AI AGENT v2 - CONFIGURATION
# Fill in your API keys and settings below
# ============================================================

import os

# --- GOOGLE GEMINI AI (FREE) ---
# Get free API key at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key")

# --- SHOPIFY ---
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL", "your-store.myshopify.com")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN", "your_shopify_admin_token")
SHOPIFY_WEBHOOK_SECRET = os.getenv("SHOPIFY_WEBHOOK_SECRET", "your_webhook_secret")

# --- EMAIL (Gmail SMTP) ---
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "your_gmail@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your_gmail_app_password")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "your_approval_email@gmail.com")

# --- APPROVAL SERVER ---
SERVER_BASE_URL = os.getenv("SERVER_BASE_URL", "http://localhost:8000")

# --- AGENT SETTINGS ---
SEARCH_KEYWORDS = [
    "home decor", "wall art", "decorative vase", "candle holder",
    "throw pillow", "wall clock", "picture frame", "table lamp",
    "indoor plant pot", "decorative tray", "boho decor", "minimalist decor",
    "wooden decor", "brass decor", "handmade home decor", "ethnic home decor",
    "festive decor", "terracotta decor", "jute decor", "marble decor"
]

MIN_RATING         = 4.0   # Minimum product rating
MIN_PROFIT_MARGIN  = 30    # Minimum profit margin %
MAX_SUPPLIER_PRICE = 2000  # Max price in INR from supplier
PRODUCTS_PER_RUN   = 20    # Products to find per scheduled run
SCHEDULE_HOUR      = 7     # Run agent at 7 AM daily
PRODUCT_EXPIRY_DAYS = 60   # Auto-remove after 2 months
AGENT_TAG = "dropship-agent"
