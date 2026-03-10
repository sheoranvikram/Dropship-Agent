"""
agent/searcher.py - Searches all Indian platforms, deduplicates, checks stock
"""

import random
from config import SEARCH_KEYWORDS, MAX_SUPPLIER_PRICE, PRODUCTS_PER_RUN
from integrations.indiamart import search_products as search_indiamart
from integrations.tradeindia import search_products as search_tradeindia
from integrations.meesho import search_products as search_meesho
from integrations.glowroad import search_products as search_glowroad
from agent.analyzer import analyze_product
import database


def is_duplicate(title: str, supplier_url: str) -> bool:
    """Check if a product already exists in DB or on Shopify (by title/URL)."""
    return database.product_exists(title=title, supplier_url=supplier_url)


def search_all_platforms() -> list:
    """Search all Indian platforms, analyze, deduplicate, and return top products."""
    print("\n🔍 Searching Indian supplier platforms...")

    all_raw = []
    keywords = random.sample(SEARCH_KEYWORDS, min(5, len(SEARCH_KEYWORDS)))

    for keyword in keywords:
        print(f"\n  Keyword: '{keyword}'")

        for search_fn, name in [
            (search_indiamart, "IndiaMart"),
            (search_tradeindia, "TradeIndia"),
            (search_meesho, "Meesho"),
            (search_glowroad, "GlowRoad"),
        ]:
            try:
                results = search_fn(keyword, max_price=MAX_SUPPLIER_PRICE, limit=5)
                all_raw.extend(results)
            except Exception as e:
                print(f"    [{name}] Error: {e}")

    print(f"\n📦 Total raw products: {len(all_raw)}")
    print("🤖 Analyzing with Gemini AI + deduplication...\n")

    scored = []
    seen_titles = set()

    for i, product in enumerate(all_raw):
        title = product.get("title", "").strip().lower()
        url = product.get("supplier_url", "")

        # Skip duplicates within this batch
        if title in seen_titles:
            continue
        seen_titles.add(title)

        # Skip products already in our DB or Shopify
        if is_duplicate(title, url):
            print(f"  ⏭️  Skipping duplicate: {product.get('title', '')[:50]}")
            continue

        print(f"  Analyzing {i+1}/{len(all_raw)}: {product.get('title', '')[:55]}...")
        analyzed = analyze_product(product)
        if analyzed:
            scored.append(analyzed)
            print(f"    ✅ Score: {analyzed.get('score')}/10 | Margin: {analyzed.get('profit_margin')}%")
        else:
            print(f"    ❌ Filtered")

    scored.sort(key=lambda x: x.get("score", 0), reverse=True)
    top = scored[:PRODUCTS_PER_RUN]
    print(f"\n✨ {len(top)} products ready for your approval!")
    return top
