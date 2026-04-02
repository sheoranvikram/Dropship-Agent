import requests
from bs4 import BeautifulSoup
import re
import os
import time

SCRAPERAPI_KEY = os.environ.get("SCRAPERAPI_KEY", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

def scrape_url(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            return r
    except Exception:
        pass
    time.sleep(2)
    params = {"api_key": SCRAPERAPI_KEY, "url": url}
    return requests.get("http://api.scraperapi.com", params=params, timeout=60)

def search_products(keyword: str, max_price: float = 2000, limit: int = 10) -> list:
    url = f"https://www.tradeindia.com/search.html?query={keyword.replace(' ', '+')}"
    try:
        time.sleep(2)
        response = scrape_url(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
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

            digits = re.sub(r"[^\d]", "", (price_el.get_text(strip=True) if price_el else "600").split("-")[0])
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

        print(f"    [TradeIndia] Found {len(products)} products for '{keyword}'")
        return products
    except Exception as e:
        print(f"    [TradeIndia] Error searching '{keyword}': {e}")
        return []

def check_availability(supplier_url: str) -> dict:
    try:
        r = requests.get(supplier_url, headers=HEADERS, timeout=20)
        page_text = r.text.lower()
        if "page not found" in page_text or "not available" in page_text:
            return {"available": False, "in_stock": False}
        return {"available": True, "in_stock": "out of stock" not in page_text}
    except Exception:
        return {"available": False, "in_stock": False}
