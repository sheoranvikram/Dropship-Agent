"""
integrations/tradeindia.py - Search home decor products on TradeIndia
Tries without JS rendering first (1 credit), falls back to rendered (10 credits).
"""

import requests
from bs4 import BeautifulSoup
import re
import os
import time

SCRAPERAPI_KEY = os.environ.get("SCRAPERAPI_KEY", "")

DIRECT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}


def scrape_url(url: str, render: bool = False) -> requests.Response:
    params = {
        "api_key": SCRAPERAPI_KEY,
        "url": url,
    }
    if render:
        params["render"] = "true"
    return requests.get("http://api.scraperapi.com", params=params, timeout=60)


def _parse_products(soup, max_price, limit):
    products = []
    blocks = (
        soup.find_all("div", class_=re.compile(r"product.?box|product.?card|listing.?item", re.I))
        or soup.find_all("li", class_=re.compile(r"product|listing|item", re.I))
        or soup.find_all("div", class_=re.compile(r"product|listing|card|item", re.I))
    )

    for block in blocks[:limit * 3]:
        title_el = (
            block.find(["h2", "h3", "h4"], class_=re.compile(r"title|name|product", re.I))
            or block.find("a", class_=re.compile(r"title|name|product", re.I))
            or block.find(["h2", "h3", "h4"])
        )
        price_el = block.find(class_=re.compile(r"price|prc|cost|rate|rupee", re.I))
        link_el = block.find("a", href=True)
        img_el = block.find("img")

        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        if len(title) < 5:
            continue

        price_text = price_el.get_text(strip=True) if price_el else "600"
        digits = re.sub(r"[^\d]", "", price_text.split("-")[0])
        price = float(digits) if digits else 600.0
        if price > max_price:
            continue

        link = link_el["href"] if link_el else ""
        if link and not link.startswith("http"):
            link = "https://www.tradeindia.com" + link

        image = ""
        if img_el:
            image = img_el.get("data-src") or img_el.get("data-original") or img_el.get("src", "")

        products.append({
            "title": title,
            "supplier": "TradeIndia",
            "supplier_url": link,
            "supplier_price": price,
            "images": [image] if image else [],
            "rating": 4.1,
            "orders": 0,
            "item_id": link,
        })

        if len(products) >= limit:
            break

    return products


def search_products(keyword: str, max_price: float = 2000, limit: int = 10) -> list:
    query = keyword.replace(" ", "+")
    url = f"https://www.tradeindia.com/search.html?query={query}"

    try:
        # --- Attempt 1: Direct request (0 credits) ---
        time.sleep(2)
        try:
            r = requests.get(url, headers=DIRECT_HEADERS, timeout=20)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                products = _parse_products(soup, max_price, limit)
                if products:
                    print(f"    [TradeIndia] Found {len(products)} products for '{keyword}'")
                    return products
        except Exception:
            pass

        # --- Attempt 2: ScraperAPI without rendering (1 credit) ---
        time.sleep(2)
        response = scrape_url(url, render=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        products = _parse_products(soup, max_price, limit)

        # --- Attempt 3: ScraperAPI with JS rendering (10 credits) ---
        if not products:
            time.sleep(3)
            response = scrape_url(url, render=True)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            products = _parse_products(soup, max_price, limit)

        print(f"    [TradeIndia] Found {len(products)} products for '{keyword}'")
        return products

    except Exception as e:
        print(f"    [TradeIndia] Error searching '{keyword}': {e}")
        return []


def check_availability(supplier_url: str) -> dict:
    try:
        time.sleep(1)
        r = requests.get(url=supplier_url, headers=DIRECT_HEADERS, timeout=20)
        page_text = r.text.lower()
        if "page not found" in page_text or "not available" in page_text:
            return {"available": False, "in_stock": False}
        out_of_stock = "out of stock" in page_text
        return {"available": True, "in_stock": not out_of_stock}
    except Exception:
        return {"available": False, "in_stock": False}
