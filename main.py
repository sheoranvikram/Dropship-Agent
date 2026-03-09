"""
main.py - Entry point for Dropship AI Agent v2

Usage:
  python main.py             # Run once immediately
  python main.py --schedule  # Run daily at 7 AM
  python main.py --setup     # Register Shopify webhook only
"""

import sys
import time
import schedule
from datetime import datetime

import database
from agent.searcher import search_all_platforms
from agent.stock_checker import check_all_listed_products, remove_expired_products
from email.sender import send_approval_email
from integrations.shopify import register_order_webhook
from config import SCHEDULE_HOUR, SERVER_BASE_URL


def run_agent():
    print(f"\n{'='*60}")
    print(f"  🤖 DROPSHIP AI AGENT v2")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    database.init_db()

    # Step 1: Remove expired products (2 months old)
    remove_expired_products()

    # Step 2: Check stock of existing listed products
    check_all_listed_products()

    # Step 3: Search and analyze new products
    products = search_all_platforms()

    if not products:
        print("\n⚠️  No new products found. Try adjusting config.py filters.")
        return

    # Step 4: Save to DB
    print(f"\n💾 Saving {len(products)} products to database...")
    for product in products:
        pid = database.save_product(product)
        product["id"] = pid

    # Step 5: Send approval email
    print(f"\n📧 Sending approval email...")
    send_approval_email(products)

    print(f"\n{'='*60}")
    print(f"  ✅ DONE — {len(products)} products sent for your approval")
    print(f"  Make sure approval server is running: uvicorn server:app --port 8000")
    print(f"{'='*60}\n")


def setup_webhook():
    """Register Shopify order webhook."""
    database.init_db()
    print(f"Registering Shopify order webhook → {SERVER_BASE_URL}/webhook/order")
    success = register_order_webhook(SERVER_BASE_URL)
    if success:
        print("✅ Webhook registered! You'll now receive order emails automatically.")
    else:
        print("❌ Webhook registration failed. Check Shopify credentials in config.py.")


def run_scheduled():
    print(f"⏰ Scheduler started. Agent runs daily at {SCHEDULE_HOUR}:00 AM")
    schedule.every().day.at(f"{SCHEDULE_HOUR:02d}:00").do(run_agent)
    run_agent()  # Run immediately on start
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    if "--setup" in sys.argv:
        setup_webhook()
    elif "--schedule" in sys.argv:
        run_scheduled()
    else:
        database.init_db()
        run_agent()
