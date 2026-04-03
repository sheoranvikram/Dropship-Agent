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
        
        # DEBUG - print first 500 chars of text and all unique class names
        print(f"    [IndiaMart DEBUG] Status: {response.status_code}, HTML length: {len(response.text)}")
        print(f"    [IndiaMart DEBUG] Page text preview: {soup.get_text()[:300].strip()}")
        all_classes = set()
        for tag in soup.find_all(class_=True):
            for c in tag.get("class", []):
                all_classes.add(c)
        print(f"    [IndiaMart DEBUG] Classes found: {list(all_classes)[:30]}")
        
        print(f"    [IndiaMart] Found 0 products for '{keyword}'")
        return []
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
