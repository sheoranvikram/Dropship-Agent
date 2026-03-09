# 🛒 Dropship AI Agent v2 — India Edition

Fully automated home decor dropshipping agent for Indian suppliers + Indian customers.

## What It Does

- 🔍 Searches IndiaMart, TradeIndia, Meesho, GlowRoad daily at 7 AM
- 🤖 Scores & writes product descriptions using FREE Google Gemini AI
- 🚫 Skips duplicate products already on your store
- 📧 Emails you product cards with Approve / Edit & Approve / Reject buttons
- ✏️ Edit price, title, description before approving
- ✅ Auto-lists approved products to Shopify as drafts
- 📦 Emails you instantly when a new order arrives (with full customer details)
- 📊 Checks stock availability daily
- 🗑️ Auto-removes products older than 2 months
- 🚫 Never mentions return or replacement policy

## Setup (5 steps)

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Fill in config.py
| Key | Where to get |
|-----|-------------|
| GEMINI_API_KEY | https://aistudio.google.com/app/apikey (FREE) |
| SHOPIFY_STORE_URL | your-store.myshopify.com |
| SHOPIFY_ACCESS_TOKEN | Shopify Admin → Settings → Apps → Develop Apps |
| SHOPIFY_WEBHOOK_SECRET | Any random string — paste same in Shopify webhook settings |
| EMAIL_SENDER | Your Gmail |
| EMAIL_PASSWORD | Gmail App Password (Google Account → Security → App Passwords) |
| EMAIL_RECEIVER | Where to receive approval + order emails |
| SERVER_BASE_URL | Your server URL (use ngrok for local dev) |

### 3. Start the Approval Server
```bash
# Terminal 1
uvicorn server:app --host 0.0.0.0 --port 8000

# For local dev, expose via ngrok (Terminal 2)
ngrok http 8000
# Copy the https://xxx.ngrok.io URL to SERVER_BASE_URL in config.py
```

### 4. Register Shopify Order Webhook
```bash
python main.py --setup
```

### 5. Run the Agent
```bash
# Run once
python main.py

# Run on schedule (daily at 7 AM)
python main.py --schedule
```

## Cost
| Component | Cost |
|-----------|------|
| Gemini AI (product scoring) | FREE (1500 req/day) |
| All supplier platforms | FREE (scraping) |
| Gmail SMTP | FREE |
| Shopify API | FREE (with your existing plan) |
| Server hosting | FREE (your PC) or ~₹400/month (VPS) |
| **Total** | **₹0/month** |

## Key Features Summary
- ✅ 7 AM daily schedule
- ✅ 20 products per run
- ✅ No duplicates ever listed
- ✅ Edit price/title/description before approving
- ✅ Order email with full customer details for manual forwarding
- ✅ No return/replacement policy in descriptions
- ✅ 2-month-old products auto-removed
- ✅ Daily stock availability check
- ✅ Completely free to run
