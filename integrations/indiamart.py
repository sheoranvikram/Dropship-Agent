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
        seen_urls = set()

        product_links = soup.find_all("a", href=re.compile(
            r"(indiamart\.com/(proddetail|trade|catalog)|dir\.indiamart\.com/)", re.I
        ))

        for link_el in product_links:
            href = link_el.get("href", "")
            if not href or href in seen_urls:
                continue
            if not href.startswith("http"):
                href = "https://www.indiamart.com" + href
            seen_urls.add(href)

            container = link_el
            for _ in range(6):
                if container.parent:
                    container = container.parent
                else:
                    break

            title = ""
            for tag in ["h2", "h3", "h4", "h5"]:
                el = container.find(tag)
                if el:
                    title = el.get_text(strip=True)
                    break
            if not title:
                title = link_el.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            price = 500.0
            price_match = re.search(r"(?:₹|Rs\.?|INR)\s*([\d,]+)", container.get_text())
            if price_match:
                price = float(price_match.group(1).replace(",", ""))
            if price > max_price:
                continue

            image = ""
            img_el = container.find("img")
            if img_el:
                image = img_el.get("data-src") or img_el.get("data-original") or img_el.get("data-lazy-src") or img_el.get("src", "")
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
