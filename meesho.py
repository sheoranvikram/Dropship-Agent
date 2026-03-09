"""
integrations/meesho.py - Search home decor products on Meesho
Scrapes Meesho's catalog pages for wholesale/reseller products
"""

import requests
from bs4 import BeautifulSoup
import re
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.meesho.com/",
}


def search_products(keyword: str, max_price: float = 2000, limit: int = 10) -> list:
    """
    Search Meesho for home decor products.
    Returns list of raw product dicts.
    """
    # Meesho has a catalog search API used by their web app
    url = "https://www.meesho.com/api/v1/products/search"
    params = {
        "query": keyword,
        "page": 1,
        "limit": limit
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)

        # Try JSON response first
        if response.status_code == 200:
            try:
                data = response.json()
                items = data.get("products", data.get("data", []))
                products = []

                for item in items[:limit]:
                    price = float(item.get("price", {}).get("mrp", 0) or
                                  item.get("mrp", 0) or 500)

                    if price > max_price:
                        continue

                    images = item.get("images", [])
                    image_urls = [img.get("url", "") for img in images if img.get("url")]

                    products.append({
                        "title": item.get("name", item.get("title", "")),
                        "supplier": "Meesho",
                        "supplier_url": f"https://www.meesho.com/p/{item.get('slug', item.get('id', ''))}",
                        "supplier_price": price,
                        "images": image_urls[:3],
                        "rating": float(item.get("rating", {}).get("average", 4.0) or 4.0),
                        "orders": item.get("orders_count", 0),
                        "item_id": str(item.get("id", ""))
                    })

                print(f"    [Meesho] Found {len(products)} products for '{keyword}'")
                return products

            except (json.JSONDecodeError, KeyError):
                pass

        # Fallback: scrape HTML
        scrape_url = f"https://www.meesho.com/search?q={keyword.replace(' ', '+')}"
        resp2 = requests.get(scrape_url, headers={**HEADERS, "Accept": "text/html"}, timeout=15)
        soup = BeautifulSoup(resp2.text, "html.parser")

        products = []
        cards = soup.find_all("div", attrs={"data-testid": re.compile(r"product", re.I)})
        if not cards:
            cards = soup.find_all("div", class_=re.compile(r"product|card|item", re.I))

        for card in cards[:limit * 2]:
            title_el = card.find(["h2", "h3", "p"], class_=re.compile(r"title|name", re.I))
            price_el = card.find(class_=re.compile(r"price|prc|cost", re.I))
            link_el = card.find("a", href=True)
            img_el = card.find("img")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if len(title) < 5:
                continue

            price_text = price_el.get_text(strip=True) if price_el else "400"
            price_match = re.search(r"[\d,]+", price_text.replace(",", ""))
            price = float(price_match.group().replace(",", "")) if price_match else 400.0

            if price > max_price:
                continue

            link = link_el["href"] if link_el else ""
            if link and not link.startswith("http"):
                link = "https://www.meesho.com" + link

            image = img_el.get("src", "") if img_el else ""

            products.append({
                "title": title,
                "supplier": "Meesho",
                "supplier_url": link,
                "supplier_price": price,
                "images": [image] if image else [],
                "rating": 4.0,
                "orders": 0,
                "item_id": link
            })

            if len(products) >= limit:
                break

        print(f"    [Meesho] Found {len(products)} products for '{keyword}'")
        return products

    except Exception as e:
        print(f"    [Meesho] Error searching '{keyword}': {e}")
        return []


def check_availability(supplier_url: str) -> dict:
    """Check if a Meesho product is still available."""
    try:
        response = requests.get(supplier_url, headers=HEADERS, timeout=10)
        page_text = response.text.lower()
        if "page not found" in page_text or "404" in page_text:
            return {"available": False, "in_stock": False}
        out_of_stock = "out of stock" in page_text or "sold out" in page_text
        return {"available": True, "in_stock": not out_of_stock}
    except Exception:
        return {"available": False, "in_stock": False}
