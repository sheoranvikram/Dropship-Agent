# ============================================================
# DROPSHIP AI AGENT v2 - CONFIGURATION
# ============================================================

import os

# --- GOOGLE GEMINI AI (FREE) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyD1FIVNhWGcgwd2H4VMKDe_gXGE0JkYDTk")

# --- SHOPIFY ---
SHOPIFY_STORE_URL    = os.getenv("SHOPIFY_STORE_URL", "https://admin.shopify.com/store/qztf8b-wf?ui_locales=en-IN")
SHOPIFY_CLIENT_ID     = os.getenv("SHOPIFY_CLIENT_ID", "f76b43178e19900c760ae592efd61628")
SHOPIFY_CLIENT_SECRET = os.getenv("SHOPIFY_CLIENT_SECRET", "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")
SHOPIFY_WEBHOOK_SECRET = os.getenv("SHOPIFY_WEBHOOK_SECRET", "vikram@store")
# Auto-filled after OAuth setup — do not edit manually
SHOPIFY_ACCESS_TOKEN  = os.getenv("SHOPIFY_ACCESS_TOKEN", "")

# --- EMAIL (Gmail SMTP) ---
EMAIL_SENDER   = os.getenv("EMAIL_SENDER", "sheoranvikram499@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "njedntaxvyljjjad")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "sheoranvikram499@gmail.com")

# --- APPROVAL SERVER ---
SERVER_BASE_URL = os.getenv("SERVER_BASE_URL", "web-production-a1b2f1.up.railway.app")

# --- AGENT SETTINGS ---
SEARCH_KEYWORDS = [
    "home decor", "wall art", "decorative vase", "candle holder",
    "throw pillow", "wall clock", "picture frame", "table lamp",
    "indoor plant pot", "decorative tray", "boho decor", "minimalist decor",
    "wooden decor", "brass decor", "handmade home decor", "ethnic home decor",
    "festive decor", "terracotta decor", "jute decor", "marble decor"
]

MIN_RATING          = 4.0   # Minimum product rating
MIN_PROFIT_MARGIN   = 30    # Minimum profit margin %
MAX_SUPPLIER_PRICE  = 2000  # Max price in INR from supplier
PRODUCTS_PER_RUN    = 20    # Products to find per scheduled run
SCHEDULE_HOUR       = 7     # Run agent at 7 AM daily
PRODUCT_EXPIRY_DAYS = 60    # Auto-remove after 2 months

AGENT_TAG           = "dropship-agent"
