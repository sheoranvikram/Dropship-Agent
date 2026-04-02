"""
integrations/meesho.py - Search home decor products on Meesho
Uses Meesho's internal catalogue API directly — no ScraperAPI credits needed.
"""

import requests
import re
import time

# Meesho's internal search API (no auth required, mimics browser headers)
MEESHO_API = "https://meesho.com/api/v1/products/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.meesho.com/",
    "Origin": "https://www.meesho.com",
    "x-meta-app": '{"appVersion":"5.0.0"}',
}


def _api_search(keyword: str, max_price: float, limit: int) -> list:
    """
    Hit Meesho's internal search API.
    Returns parsed product list or empty list if it fails.
    """
    payload = {
        "query": keyword,
        "page": 1,
        "pageSize": min(limit * 2, 40),
        "filters": {},
        "sortBy": "RELEVANCE",
    }
    try:
        r = requests.post(
            MEESHO_API,
            json=payload,
            headers=HEADERS,
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    # Response shape: {"data": {"products": [...]}}
    raw_items = (
        data.get("data", {}).get("products", [])
        or data.get("products", [])
        or []
    )

    products = []
    for item in raw_items:
        try:
            # Price lives under product_variants[0] or top-level
            variants = item.get("product_variants", [{}])
            price = float(
                (variants[0].get("selling_price") if variants else None)
                or item.get("selling_price")
                or item.get("mrp")
                or 400
            )
            if price > max_price:
                continue

            # Images
            images_raw = item.get("images", []) or variants[0].get("images", []) if variants else []
            images = []
            for img in images_raw:
                src = img.get("url") or img.get("src") or (img if isinstance(img, str) else "")
                if src:
                    images.append(src)

            rating_raw = item.get("rating")
            rating = float(
                rating_raw.get("average", 4.0) if isinstance(rating_raw, dict) else (rating_raw or 4.0)
            )

            slug = item.get("slug") or item.get("id") or ""
            products.append({
                "title": item.get("name") or item.get("title") or "",
                "supplier": "Meesho",
                "supplier_url": f"https://www.meesho.com/p/{slug}",
                "supplier_price": price,
                "images": images[:3],
                "rating": rating,
                "orders": item.get("orders_count", 0),
                "item_id": str(item.get("id", slug)),
            })

            if len(products) >= limit:
                break

        except (TypeError, KeyError, IndexError, ValueError):
            continue

    return products


def _scrape_search(keyword: str, max_price: float, limit: int) -> list:
    """
    Fallback: scrape Meesho search page WITHOUT ScraperAPI.
    Meesho injects __NEXT_DATA__ JSON into the page on server-side renders
    for some search queries.
    """
    import json
    from bs4 import BeautifulSoup

    url = f"https://www.meesho.com/search?q={keyword.replace(' ', '%20')}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")

        script = soup.find("script", id="__NEXT_DATA__")
        if not script:
            return []

        data = json.loads(script.string)
        props = data.get("props", {}).get("pageProps", {})
        items = (
            props.get("catalogListingResult", {}).get("products", [])
            or props.get("searchResult", {}).get("products", [])
            or props.get("products", [])
        )

        products = []
        for item in items:
            price = float(item.get("price", {}).get("mrp", 0) or item.get("mrp", 400) or 400)
            if price > max_price:
                continue
            images_raw = item.get("images", [])
            images = [
                (img.get("url") or img.get("src") or "")
                for img in images_raw if isinstance(img, dict)
            ]
            slug = item.get("slug") or item.get("id") or ""
            products.append({
                "title": item.get("name") or item.get("title") or "",
                "supplier": "Meesho",
                "supplier_url": f"https://www.meesho.com/p/{slug}",
                "supplier_price": price,
                "images": [i for i in images if i][:3],
                "rating": 4.0,
                "orders": item.get("orders_count", 0),
                "item_id": str(item.get("id", slug)),
            })
            if len(products) >= limit:
                break
        return products

    except Exception:
        return []


def search_products(keyword: str, max_price: float = 2000, limit: int = 10) -> list:
    time.sleep(2)

    # Try internal API first (fastest, no credits used)
    products = _api_search(keyword, max_price, limit)

    # Fallback to page scrape
    if not products:
        time.sleep(2)
        products = _scrape_search(keyword, max_price, limit)

    # Filter out blank titles
    products = [p for p in products if p.get("title") and len(p["title"]) >= 5]

    print(f"    [Meesho] Found {len(products)} products for '{keyword}'")
    return products


def check_availability(supplier_url: str) -> dict:
    try:
        time.sleep(1)
        r = requests.get(supplier_url, headers=HEADERS, timeout=20)
        page_text = r.text.lower()
        if "page not found" in page_text or "404" in page_text:
            return {"available": False, "in_stock": False}
        out_of_stock = "out of stock" in page_text or "sold out" in page_text
        return {"available": True, "in_stock": not out_of_stock}
    except Exception:
        return {"available": False, "in_stock": False}
