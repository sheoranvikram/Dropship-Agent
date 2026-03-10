"""
integrations/glowroad.py - Search home decor products on GlowRoad
GlowRoad is an Indian dropshipping/reseller platform
"""

import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
}


def search_products(keyword: str, max_price: float = 2000, limit: int = 10) -> list:
    """
    Search GlowRoad for home decor products.
    Returns list of raw product dicts.
    """
    url = f"https://glowroad.com/search?q={keyword.replace(' ', '+')}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        products = []
        cards = soup.find_all("div", class_=re.compile(r"product|card|item|listing", re.I))

        for card in cards[:limit * 2]:
            title_el = card.find(["h2", "h3", "a", "span"], class_=re.compile(r"title|name|product", re.I))
            price_el = card.find(class_=re.compile(r"price|prc|cost|selling", re.I))
            link_el = card.find("a", href=True)
            img_el = card.find("img")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if len(title) < 5:
                continue

            price_text = price_el.get_text(strip=True) if price_el else "450"
            price_match = re.search(r"[\d,]+", price_text.replace(",", ""))
            price = float(price_match.group().replace(",", "")) if price_match else 450.0

            if price > max_price:
                continue

            link = link_el["href"] if link_el else ""
            if link and not link.startswith("http"):
                link = "https://glowroad.com" + link

            image = ""
            if img_el:
                image = img_el.get("data-src") or img_el.get("src", "")

            products.append({
                "title": title,
                "supplier": "GlowRoad",
                "supplier_url": link,
                "supplier_price": price,
                "images": [image] if image else [],
                "rating": 4.3,
                "orders": 0,
                "item_id": link
            })

            if len(products) >= limit:
                break

        print(f"    [GlowRoad] Found {len(products)} products for '{keyword}'")
        return products

    except Exception as e:
        print(f"    [GlowRoad] Error searching '{keyword}': {e}")
        return []


def check_availability(supplier_url: str) -> dict:
    """Check if a GlowRoad product is still available."""
    try:
        response = requests.get(supplier_url, headers=HEADERS, timeout=10)
        page_text = response.text.lower()
        if "page not found" in page_text or "404" in page_text:
            return {"available": False, "in_stock": False}
        out_of_stock = "out of stock" in page_text or "sold out" in page_text
        return {"available": True, "in_stock": not out_of_stock}
    except Exception:
        return {"available": False, "in_stock": False}
