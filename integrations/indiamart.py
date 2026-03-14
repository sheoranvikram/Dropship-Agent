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
        "render": "true",
        "country_code": "in",
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

        # DEBUG: print all unique div class names so we can find the right ones
        all_divs = soup.find_all("div", class_=True)
        class_names = set()
        for d in all_divs:
            for c in d.get("class", []):
                class_names.add(c)
        print(f"    [IndiaMart DEBUG] Total divs: {len(all_divs)} | Unique classes (sample): {list(class_names)[:40]}")

        products = []

        # Strategy 1: look for divs that contain an imimg.com image (product images)
        # We know from previous debug that product images are hosted on 5.imimg.com
        all_links = soup.find_all("a", href=re.compile(r"indiamart\.com", re.I))
        print(f"    [IndiaMart DEBUG] Total IndiaMart links found: {len(all_links)}")

        seen = set()
        for link_el in all_links:
            href = link_el.get("href", "")
            # Skip navigation/footer links - product links usually have long paths
            if len(href) < 30:
                continue
            if href in seen:
                continue
            seen.add(href)

            # Get title from link text or nearby heading
            title = link_el.get_text(strip=True)
            if not title or len(title) < 5:
                # Try parent
                parent = link_el.parent
                if parent:
                    title = parent.get_text(strip=True)[:100]

            if not title or len(title) < 5:
                continue

            # Try to find price near this link
            parent = link_el.parent
            price = 500.0
            for _ in range(4):  # walk up 4 levels
                if parent is None:
                    break
                price_el = parent.find(string=re.compile(r"₹|Rs\.?|INR", re.I))
                if price_el:
                    digits = re.sub(r"[^\d]", "", str(price_el).split("-")[0])
                    if digits:
                        price = float(digits[:6])  # cap to avoid parsing huge numbers
                    break
                parent = parent.parent

            if price > max_price:
                continue

            # Try to find image near this link
            image = ""
            parent = link_el.parent
            for _ in range(4):
                if parent is None:
                    break
                img_el = parent.find("img")
                if img_el:
                    image = img_el.get("data-src") or img_el.get("data-original") or img_el.get("src", "")
                    break
                parent = parent.parent

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
        response = scrape_url(supplier_url)
        page_text = response.text.lower()
        if "page not found" in page_text or "product not available" in page_text:
            return {"available": False, "in_stock": False}
        out_of_stock = "out of stock" in page_text or "not available" in page_text
        return {"available": True, "in_stock": not out_of_stock}
    except Exception:
        return {"available": False, "in_stock": False}
