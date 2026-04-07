"""
integrations/indiamart.py - Now scrapes Flipkart (IndiaMart was unreliable)
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
    url = f"https://www.flipkart.com/search?q={query}&sort=popularity"
    try:
        time.sleep(2)
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        products = []

        # Flipkart product cards have a consistent structure
        cards = soup.find_all("div", attrs={"data-id": True})
        if not cards:
            # fallback selector
            cards = soup.find_all("div", class_=re.compile(r"_1AtVbE|_13oc-S|_4ddWXP", re.I))

        for card in cards:
            title_el = card.find(["div","a"], class_=re.compile(r"_4rR01T|s1Q9rs|_2WkVRV|IRpwTa", re.I))
            price_el = card.find(["div","span"], class_=re.compile(r"_30jeq3|_1_WHN1|_3I9_wc", re.I))
            link_el = card.find("a", href=True)
            img_el = card.find("img")

            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if len(title) < 5:
                continue

            price_text = price_el.get_text(strip=True) if price_el else "0"
            digits = re.sub(r"[^\d]", "", price_text)
            price = float(digits) if digits else 0.0
            if price == 0 or price > max_price:
                continue

            link = link_el["href"] if link_el else ""
            if link and not link.startswith("http"):
                link = "https://www.flipkart.com" + link

            image = ""
            if img_el:
                image = img_el.get("src") or img_el.get("data-src", "")

            products.append({
                "title": title[:150],
                "supplier": "Flipkart",
                "supplier_url": link,
                "supplier_price": price,
                "images": [image] if image else [],
                "rating": 4.2,
                "orders": 0,
                "item_id": link,
            })
            if len(products) >= limit:
                break

        print(f"    [Flipkart] Found {len(products)} products for '{keyword}'")
        return products
    except Exception as e:
        print(f"    [Flipkart] Error searching '{keyword}': {e}")
        return []

def check_availability(supplier_url: str) -> dict:
    try:
        r = requests.get(supplier_url, headers=HEADERS, timeout=20)
        page_text = r.text.lower()
        if "page not found" in page_text or "404" in page_text:
            return {"available": False, "in_stock": False}
        return {"available": True, "in_stock": "out of stock" not in page_text and "sold out" not in page_text}
    except Exception:
        return {"available": False, "in_stock": False}
