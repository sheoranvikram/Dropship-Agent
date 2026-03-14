"""
integrations/glowroad.py - Search home decor products on GlowRoad
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
        "render": "true",
        "country_code": "in",
        "device_type": "desktop",
    }
    return requests.get(api_url, params=params, timeout=60)


def search_products(keyword: str, max_price: float = 2000, limit: int = 10) -> list:
    """
    Search GlowRoad for home decor products.
    Returns list of raw product dicts.
    """
    url = f"https://glowroad.com/search?q={keyword.replace(' ', '+')}"

    try:
        response = scrape_url(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        products = []

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
        response = scrape_url(supplier_url)
        page_text = response.text.lower()
        if "page not found" in page_text or "404" in page_text:
            return {"available": False, "in_stock": False}
        out_of_stock = "out of stock" in page_text or "sold out" in page_text
        return {"available": True, "in_stock": not out_of_stock}
    except Exception:
        return {"available": False, "in_stock": False}
