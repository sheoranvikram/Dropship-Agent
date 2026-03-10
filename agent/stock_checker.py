"""
agent/stock_checker.py - Daily availability and stock check for listed products
Removes unavailable products from Shopify and marks them in DB
"""

import database
from integrations.shopify import delete_product
from integrations.indiamart import check_availability as check_indiamart
from integrations.tradeindia import check_availability as check_tradeindia
from integrations.meesho import check_availability as check_meesho
from integrations.glowroad import check_availability as check_glowroad
from config import PRODUCT_EXPIRY_DAYS


CHECKER_MAP = {
    "IndiaMart": check_indiamart,
    "TradeIndia": check_tradeindia,
    "Meesho": check_meesho,
    "GlowRoad": check_glowroad,
}


def check_all_listed_products() -> dict:
    """
    Check availability of all listed products.
    Returns summary dict.
    """
    print("\n🔎 Checking stock & availability for all listed products...")

    listed = database.get_pending_products()
    # Also check listed ones
    import sqlite3, json
    conn = sqlite3.connect(database.DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE status = 'listed'")
    rows = c.fetchall()
    conn.close()
    listed_products = [dict(r) for r in rows]

    removed = []
    unavailable = []

    for product in listed_products:
        supplier = product.get("supplier", "")
        url = product.get("supplier_url", "")
        checker = CHECKER_MAP.get(supplier)

        if not checker or not url:
            continue

        result = checker(url)

        if not result.get("available") or not result.get("in_stock"):
            print(f"  ❌ Unavailable: {product['title'][:55]} [{supplier}]")
            unavailable.append(product)

            # Remove from Shopify
            if product.get("shopify_product_id"):
                deleted = delete_product(product["shopify_product_id"])
                if deleted:
                    database.update_product_status(product["id"], "removed")
                    removed.append(product["title"])
                    print(f"     🗑️  Removed from Shopify")
        else:
            print(f"  ✅ In stock: {product['title'][:55]}")

    print(f"\n📊 Stock check complete: {len(unavailable)} unavailable, {len(removed)} removed from Shopify")
    return {"unavailable": len(unavailable), "removed": removed}


def remove_expired_products() -> list:
    """
    Remove agent-added products older than PRODUCT_EXPIRY_DAYS from Shopify.
    Returns list of removed product titles.
    """
    print(f"\n🗓️  Checking for products older than {PRODUCT_EXPIRY_DAYS} days...")
    old_products = database.get_listed_products_older_than(PRODUCT_EXPIRY_DAYS)
    removed = []

    for product in old_products:
        if product.get("shopify_product_id"):
            deleted = delete_product(product["shopify_product_id"])
            if deleted:
                database.update_product_status(product["id"], "expired")
                removed.append(product["title"])
                print(f"  🗑️  Expired & removed: {product['title'][:55]}")

    print(f"  Removed {len(removed)} expired products")
    return removed
