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
    # Try direct first
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            return r
    except Exception:
        pass
    # Fallback to ScraperAPI (no render, 1 credit)
    time.sleep(2)
    params = {"api_key": SCRAPERAPI_KEY, "url": url}
    return requests.get("http://api.scraperapi.com", params=params, timeout=60)

def search_products(keyword: str, max_price: float = 2000, limit: int = 10) -> list:
    query = keyword.replace(" ", "+")
    url = f"https://dir.indiamart.com/search.mp?ss={query}&pricemin=100&pricemax={int(max_price)}"
    try:
        time.sleep(2)
        response = scrape_url(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        products = []
        seen = set()

        # Dump all text to check what we're getting
        all_text = soup.get_text()
        if "sign in" in all_text.lower() and len(all_text) < 2000:
            print(f"    [IndiaMart] Got login wall, skipping")
            return []

        # Try every <a> tag with a product-like URL
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not re.search(r"indiamart\.com/(proddetail|trade|catalog|search)", href, re.I):
                continue
            if href in seen:
                continue
            seen.add(href)

            # Walk up to find a container with price and title
            node = a
            for _ in range(8):
                text = node.get_text(" ", strip=True)
                price_match = re.search(r"(?:₹|Rs\.?|INR)\s*([\d,]+)", text)
                title_candidates = [
                    el.get_text(strip=True)
                    for el in node.find_all(["h2","h3","h4","h5","b","strong"])
                    if len(el.get_text(strip=True)) > 8
                ]
                if price_match and title_candidates:
                    price = float(price_match.group(1).replace(",", ""))
                    if price > max_price:
                        break
                    title = title_candidates[0]
                    img = node.find("img")
                    image = ""
                    if img:
                        image = img.get("data-src") or img.get("data-original") or img.get("src","")
                        if image.startswith("data:"):
                            image = ""
                    products.append({
                        "title": title[:150],
                        "supplier": "IndiaMart",
                        "supplier_url": href,
                        "supplier_price": price,
                        "images": [image] if image else [],
                        "rating": 4.2,
                        "orders": 0,
                        "item_id": href,
                    })
                    break
                if node.parent:
                    node = node.parent
                else:
                    break

            if len(products) >= limit:
                break

        print(f"    [IndiaMart] Found {len(products)} products for '{keyword}'")
        return products
    except Exception as e:
        print(f"    [IndiaMart] Error searching '{keyword}': {e}")
        return []
def check_availability(supplier_url: str) -> dict:
    try:
        r = requests.get(supplier_url, headers=HEADERS, timeout=20)
        page_text = r.text.lower()
        if "page not found" in page_text or "product not available" in page_text:
            return {"available": False, "in_stock": False}
        return {"available": True, "in_stock": "out of stock" not in page_text}
    except Exception:
        return {"available": False, "in_stock": False}
