"""
integrations/glowroad.py - Search home decor products on GlowRoad
Uses improved session + headers to avoid 403 blocks
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
        "Referer": "https://glowroad.com/",
    })
    return session


def search_products(keyword: str, max_price: float = 2000, limit: int = 10) -> list:
    """
    Search GlowRoad for home decor products.
    Returns list of raw product dicts.
    """
    session = get_session()

    try:
        # Visit homepage first to get cookies
        session.get("https://glowroad.com/", timeout=10)
        time.sleep(random.uniform(1.0, 2.0))

        url = f"https://glowroad.com/search?q={keyword.replace(' ', '+')}"
        response = session.get(url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        products = []

        # Try multiple selector strategies
        cards = (
            soup.find_all("div", class_=re.compile(r"product.?card|product.?item|catalog.?item", re.I))
            or soup.find_all("div", attrs={"data-product-id": True})
            or soup.find_all("div", class_=re.compile(r"product|card|item|listing", re.I))
        )

        for card in cards[:limit * 3]:
            title_el = card.find(
                ["h2", "h3", "a", "span", "p"],
                class_=re.compile(r"title|name|product.?name", re.I)
            )
            price_el = card.find(class_=re.compile(r"price|prc|cost|selling|sell.?price", re.I))
            link_el = card.find("a", href=True)
            img_el = card.find("img")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if len(title) < 5:
                continue

            price_text = price_el.get_text(strip=True) if price_el else "450"
            digits = re.sub(r"[^\d]", "", price_text.split("-")[0])
            price = float(digits) if digits else 450.0

            if price > max_price:
                continue

            link = link_el["href"] if link_el else ""
            if link and not link.startswith("http"):
                link = "https://glowroad.com" + link

            image = ""
            if img_el:
                image = img_el.get("data-src") or img_el.get("data-original") or img_el.get("src", "")

            products.append({
                "title": title,
                "supplier": "GlowRoad",
                "supplier_url": link,
                "supplier_price": price,
                "images": [image] if image else [],
                "rating": 4.3,
                "orders": 0,
                "item_id": link,
            })

            if len(products) >= limit:
                break

        print(f"    [GlowRoad] Found {len(products)} products for '{keyword}'")
        return products

    except Exception as e:
        print(f"    [GlowRoad] Error searching '{keyword}': {e}")
        return []


def check_availability(supplier_url: str) -> dict:
    try:
        session = get_session()
        response = session.get(supplier_url, timeout=10)
        page_text = response.text.lower()
        if "page not found" in page_text or "404" in page_text:
            return {"available": False, "in_stock": False}
        out_of_stock = "out of stock" in page_text or "sold out" in page_text
        return {"available": True, "in_stock": not out_of_stock}
    except Exception:
        return {"available": False, "in_stock": False}
