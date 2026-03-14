"""
integrations/indiamart.py - Search home decor products on IndiaMart
Uses IndiaMart's directory search with improved anti-block headers
"""

import requests
from bs4 import BeautifulSoup
import re
import random
import time

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

def get_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    })
    return session


def search_products(keyword: str, max_price: float = 2000, limit: int = 10) -> list:
    """
    Search IndiaMart for home decor products.
    Returns list of raw product dicts.
    """
    query = keyword.replace(" ", "+")
    # Use dir.indiamart.com - more scraper-friendly than export.indiamart.com
    url = f"https://dir.indiamart.com/search.mp?ss={query}&pricemin=100&pricemax={int(max_price)}"

    session = get_session()

    try:
        # First visit homepage to get cookies (mimics real browser)
        session.get("https://dir.indiamart.com/", timeout=10)
        time.sleep(random.uniform(1.0, 2.5))

        response = session.get(url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        products = []

        # IndiaMart product cards
        listing_blocks = soup.find_all("div", class_=re.compile(r"prd|product|listing|card", re.I))

        if not listing_blocks:
            # Try alternate selectors
            listing_blocks = soup.find_all("li", class_=re.compile(r"prd|product|item", re.I))

        for block in listing_blocks[:limit * 3]:
            title_el = (
                block.find(["h2", "h3", "a"], class_=re.compile(r"title|name|prd|heading", re.I))
                or block.find("a", href=re.compile(r"indiamart\.com", re.I))
            )
            price_el = block.find(class_=re.compile(r"price|prc|cost|rupee", re.I))
            link_el = block.find("a", href=True)
            img_el = block.find("img")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if len(title) < 5:
                continue

            price_text = price_el.get_text(strip=True) if price_el else "500"
            digits = re.sub(r"[^\d]", "", price_text.split("-")[0])
            price = float(digits) if digits else 500.0

            if price > max_price:
                continue

            link = link_el["href"] if link_el else ""
            if link and not link.startswith("http"):
                link = "https://www.indiamart.com" + link

            image = ""
            if img_el:
                image = img_el.get("data-src") or img_el.get("data-original") or img_el.get("src", "")

            products.append({
                "title": title,
                "supplier": "IndiaMart",
                "supplier_url": link,
                "supplier_price": price,
                "images": [image] if image else [],
                "rating": 4.2,
                "orders": 0,
                "item_id": link,
            })

            if len(products) >= limit:
                break

        print(f"    [IndiaMart] Found {len(products)} products for '{keyword}'")
        return products

    except Exception as e:
        print(f"    [IndiaMart] Error searching '{keyword}': {e}")
        return []


def check_availability(supplier_url: str) -> dict:
    try:
        session = get_session()
        response = session.get(supplier_url, timeout=10)
        page_text = response.text.lower()
        if "page not found" in page_text or "product not available" in page_text:
            return {"available": False, "in_stock": False}
        out_of_stock = "out of stock" in page_text or "not available" in page_text
        return {"available": True, "in_stock": not out_of_stock}
    except Exception:
        return {"available": False, "in_stock": False}
