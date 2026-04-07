"""
integrations/tradeindia.py - Now scrapes Amazon India (TradeIndia was unreliable)
"""
import requests
from bs4 import BeautifulSoup
import re
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

def search_products(keyword: str, max_price: float = 2000, limit: int = 10) -> list:
    query = keyword.replace(" ", "+")
    url = f"https://www.amazon.in/s?k={query}&rh=p_36%3A10000-200000"
    try:
        time.sleep(2)
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        products = []

        cards = soup.find_all("div", attrs={"data-asin": True})

        for card in cards:
            asin = card.get("data-asin", "")
            if not asin:
                continue

            title_el = card.find("span", class_=re.compile(r"a-text-normal", re.I))
            if not title_el:
                title_el = card.find("h2")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if len(title) < 5:
                continue

            # Price
            price_el = card.find("span", class_="a-price-whole")
            price_text = price_el.get_text(strip=True) if price_el else "0"
            digits = re.sub(r"[^\d]", "", price_text)
            price = float(digits) if digits else 0.0
            if price == 0 or price > max_price:
                continue

            link = f"https://www.amazon.in/dp/{asin}"

            img_el = card.find("img", class_=re.compile(r"s-image", re.I))
            image = img_el.get("src", "") if img_el else ""

            products.append({
                "title": title[:150],
                "supplier": "Amazon India",
                "supplier_url": link,
                "supplier_price": price,
                "images": [image] if image else [],
                "rating": 4.1,
                "orders": 0,
                "item_id": asin,
            })
            if len(products) >= limit:
                break

        print(f"    [Amazon India] Found {len(products)} products for '{keyword}'")
        return products
    except Exception as e:
        print(f"    [Amazon India] Error searching '{keyword}': {e}")
        return []

def check_availability(supplier_url: str) -> dict:
    try:
        r = requests.get(supplier_url, headers=HEADERS, timeout=20)
        page_text = r.text.lower()
        if "currently unavailable" in page_text or "404" in page_text:
            return {"available": False, "in_stock": False}
        return {"available": True, "in_stock": "currently unavailable" not in page_text}
    except Exception:
        return {"available": False, "in_stock": False}
