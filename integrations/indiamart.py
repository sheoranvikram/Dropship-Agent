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
    query = keyword.replace(" ", "+")
    url = f"https://dir.indiamart.com/search.mp?ss={query}&pricemin=100&pricemax={int(max_price)}"

    try:
        response = scrape_url(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        products = []
        seen_urls = set()

        # IndiaMart product URLs follow pattern: /proddetail/ or /trade/
        product_links = soup.find_all("a", href=re.compile(
            r"(indiamart\.com/(proddetail|trade|catalog)|dir\.indiamart\.com/)",
            re.I
        ))

        print(f"    [IndiaMart DEBUG] Found {len(product_links)} product-pattern links")

        for link_el in product_links:
            href = link_el.get("href", "")
            if not href or href in seen_urls:
                continue
            if not href.startswith("http"):
                href = "https://www.indiamart.com" + href
            seen_urls.add(href)

            # Walk up the DOM to find the product card container
            container = link_el
            for _ in range(6):
                if container.parent:
                    container = container.parent
                else:
                    break

            # Get title - prefer h2/h3/h4, fallback to link text
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

            # Get price - look for rupee symbol or "Rs" anywhere in container
            price = 500.0
            price_text = container.get_text()
            # Match patterns like ₹ 250, Rs. 300, INR 400
            price_match = re.search(r"(?:₹|Rs\.?|INR)\s*([\d,]+)", price_text)
            if price_match:
                price = float(price_match.group(1).replace(",", ""))
            if price > max_price:
                continue

            # Get image
            image = ""
            img_el = container.find("img")
            if img_el:
                image = (
                    img_el.get("data-src")
                    or img_el.get("data-original")
                    or img_el.get("data-lazy-src")
                    or img_el.get("src", "")
                )
                # Skip placeholder/base64 images
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
        response = scrape_url(supplier_url)
        page_text = response.text.lower()
        if "page not found" in page_text or "product not available" in page_text:
            return {"available": False, "in_stock": False}
        out_of_stock = "out of stock" in page_text or "not available" in page_text
        return {"available": True, "in_stock": not out_of_stock}
    except Exception:
        return {"available": False, "in_stock": False}
