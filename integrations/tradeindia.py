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

        # TradeIndia product cards are usually <div class="product-info"> or similar
        # Try multiple selectors broadly
        cards = soup.find_all("div", class_=True)
        seen_titles = set()

        for card in cards:
            classes = " ".join(card.get("class", []))
            if not re.search(r"product|listing|item|card|result", classes, re.I):
                continue

            title_el = card.find(["h2","h3","h4","a"], string=re.compile(r".{8,}"))
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if len(title) < 8 or title in seen_titles:
                continue
            seen_titles.add(title)

            text = card.get_text(" ", strip=True)
            price_match = re.search(r"(?:₹|Rs\.?|INR)\s*([\d,]+)", text)
            price = float(price_match.group(1).replace(",","")) if price_match else 600.0
            if price > max_price:
                continue

            link_el = card.find("a", href=True)
            link = link_el["href"] if link_el else ""
            if link and not link.startswith("http"):
                link = "https://www.tradeindia.com" + link

            img_el = card.find("img")
            image = ""
            if img_el:
                image = img_el.get("data-src") or img_el.get("data-original") or img_el.get("src","")

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
