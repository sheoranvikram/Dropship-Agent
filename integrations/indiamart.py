"""
integrations/indiamart.py - Search home decor products on IndiaMart
Uses ScraperAPI to handle JS rendering and anti-bot protection
"""

import requests
from bs4 import BeautifulSoup
import re
import os

SCRAPERAPI_KEY = os.environ.get("SCRAPERAPI_KEY", "")


def scrape_url(url: str) -> requests.Response:
    """Fetch any URL through ScraperAPI with JS rendering enabled."""
    api_url = "http://api.scraperapi.com"
    params = {
        "api_key": SCRAPERAPI_KEY,
        "url": url,
        "render": "true",          # Execute JavaScript
        "country_code": "in",      # Indian IP address
        "device_type": "desktop",
    }
    return requests.get(api_url, params=params, timeout=60)


def search_products(keyword: str, max_price: float = 2000, limit: int = 10) -> list:
    """
    Search IndiaMart for home decor products.
    Returns list of raw product dicts.
    """
    query = keyword.replace(" ", "+")
    url = f"https://dir.indiamart.com/search.mp?ss={query}&pricemin=100&pricemax={int(max_price)}"

    try:
        response = scrape_url(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
       with open("/tmp/indiamart_debug.html", "w") as f:
    f.write(response.text)
print(f"    [IndiaMart DEBUG] Page length: {len(response.text)} | Sample: {response.text[500:2000]}")
        products = []

        # IndiaMart product card selectors
        blocks = (
            soup.find_all("div", class_=re.compile(r"prd-card|product-card|listing-card", re.I))
            or soup.find_all("div", class_=re.compile(r"prd|product|listing|card", re.I))
            or soup.find_all("li", class_=re.compile(r"prd|product|item", re.I))
        )

        for block in blocks[:limit * 3]:
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
        response = scrape_url(supplier_url)
        page_text = response.text.lower()
        if "page not found" in page_text or "product not available" in page_text:
            return {"available": False, "in_stock": False}
        out_of_stock = "out of stock" in page_text or "not available" in page_text
        return {"available": True, "in_stock": not out_of_stock}
    except Exception:
        return {"available": False, "in_stock": False}
