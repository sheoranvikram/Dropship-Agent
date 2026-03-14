"""
integrations/meesho.py - Search home decor products on Meesho
Uses ScraperAPI to handle JS rendering and anti-bot protection
"""

import requests
from bs4 import BeautifulSoup
import re
import os
import json

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
    Search Meesho for home decor products.
    Returns list of raw product dicts.
    """
    url = f"https://www.meesho.com/search?q={keyword.replace(' ', '%20')}"

    try:
        response = scrape_url(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # Try Next.js embedded JSON data first
        script_tags = soup.find_all("script", id="__NEXT_DATA__")
        if script_tags:
            try:
                data = json.loads(script_tags[0].string)
                props = data.get("props", {}).get("pageProps", {})
                items = (
                    props.get("catalogListingResult", {}).get("products", [])
                    or props.get("searchResult", {}).get("products", [])
                    or props.get("products", [])
                )
                products = []
                for item in items[:limit]:
                    price = float(
                        item.get("price", {}).get("mrp", 0)
                        or item.get("mrp", 0)
                        or item.get("selling_price", 400)
                        or 400
                    )
                    if price > max_price:
                        continue
                    images = item.get("images", [])
                    image_urls = [
                        img.get("url", "") or img.get("src", "")
                        for img in (images if isinstance(images, list) else [])
                        if isinstance(img, dict)
                    ]
                    rating_raw = item.get("rating", 4.0)
                    rating = float(rating_raw.get("average", 4.0) if isinstance(rating_raw, dict) else rating_raw or 4.0)
                    products.append({
                        "title": item.get("name", item.get("title", "")),
                        "supplier": "Meesho",
                        "supplier_url": f"https://www.meesho.com/p/{item.get('slug', item.get('id', ''))}",
                        "supplier_price": price,
                        "images": image_urls[:3],
                        "rating": rating,
                        "orders": item.get("orders_count", 0),
                        "item_id": str(item.get("id", "")),
                    })
                if products:
                    print(f"    [Meesho] Found {len(products)} products for '{keyword}'")
                    return products
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        # HTML fallback
        products = []
        cards = (
            soup.find_all("div", attrs={"data-testid": re.compile(r"product", re.I)})
            or soup.find_all("div", class_=re.compile(r"product.?card|product.?item", re.I))
            or soup.find_all("div", class_=re.compile(r"product|card|item", re.I))
        )

        for card in cards[:limit * 3]:
            title_el = card.find(
                ["h2", "h3", "p", "span"],
                class_=re.compile(r"title|name|product.?name", re.I)
            )
            price_el = card.find(class_=re.compile(r"price|prc|cost|selling", re.I))
            link_el = card.find("a", href=True)
            img_el = card.find("img")

            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if len(title) < 5:
                continue

            price_text = price_el.get_text(strip=True) if price_el else "400"
            digits = re.sub(r"[^\d]", "", price_text.split("-")[0])
            price = float(digits) if digits else 400.0

            if price > max_price:
                continue

            link = link_el["href"] if link_el else ""
            if link and not link.startswith("http"):
                link = "https://www.meesho.com" + link

            image = ""
            if img_el:
                image = img_el.get("data-src") or img_el.get("data-original") or img_el.get("src", "")

            products.append({
                "title": title,
                "supplier": "Meesho",
                "supplier_url": link,
                "supplier_price": price,
                "images": [image] if image else [],
                "rating": 4.0,
                "orders": 0,
                "item_id": link,
            })

            if len(products) >= limit:
                break

        print(f"    [Meesho] Found {len(products)} products for '{keyword}'")
        return products

    except Exception as e:
        print(f"    [Meesho] Error searching '{keyword}': {e}")
        return []


def check_availability(supplier_url: str) -> dict:
    try:
        response = scrape_url(supplier_url)
        page_text = response.text.lower()
        if "page not found" in page_text or "404" in page_text:
            return {"available": False, "in_stock": False}
        out_of_stock = "out of stock" in page_text or "sold out" in page_text
        return {"available": True, "in_stock": not out_of_stock}
    except Exception:
        return {"available": False, "in_stock": False}
