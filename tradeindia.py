"""
integrations/tradeindia.py - Search home decor products on TradeIndia
Uses TradeIndia search page scraping
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
    Search TradeIndia for home decor products.
    Returns list of raw product dicts.
    """
    query = keyword.replace(" ", "-")
    url = f"https://www.tradeindia.com/search.html?query={query}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        products = []
        blocks = soup.find_all("div", class_=re.compile(r"product|listing|card|item", re.I))

        for block in blocks[:limit * 2]:
            title_el = block.find(["h2", "h3", "h4", "a"], class_=re.compile(r"title|name|product", re.I))
            price_el = block.find(class_=re.compile(r"price|prc|cost|rate", re.I))
            link_el = block.find("a", href=True)
            img_el = block.find("img")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if len(title) < 5:
                continue

            price_text = price_el.get_text(strip=True) if price_el else "600"
            price_match = re.search(r"[\d,]+", price_text.replace(",", ""))
            price = float(price_match.group().replace(",", "")) if price_match else 600.0

            if price > max_price:
                continue

            link = link_el["href"] if link_el else ""
            if link and not link.startswith("http"):
                link = "https://www.tradeindia.com" + link

            image = ""
            if img_el:
                image = img_el.get("data-src") or img_el.get("src", "")

            products.append({
                "title": title,
                "supplier": "TradeIndia",
                "supplier_url": link,
                "supplier_price": price,
                "images": [image] if image else [],
                "rating": 4.1,
                "orders": 0,
                "item_id": link
            })

            if len(products) >= limit:
                break

        print(f"    [TradeIndia] Found {len(products)} products for '{keyword}'")
        return products

    except Exception as e:
        print(f"    [TradeIndia] Error searching '{keyword}': {e}")
        return []


def check_availability(supplier_url: str) -> dict:
    """Check if a product is still available on TradeIndia."""
    try:
        response = requests.get(supplier_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text().lower()

        if "page not found" in page_text or "not available" in page_text:
            return {"available": False, "in_stock": False}

        out_of_stock = "out of stock" in page_text
        return {"available": True, "in_stock": not out_of_stock}

    except Exception:
        return {"available": False, "in_stock": False}
