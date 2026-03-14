"""
integrations/meesho.py - Search home decor products on Meesho
Uses improved session handling to avoid blocks
"""

import requests
from bs4 import BeautifulSoup
import re
import random
import time
import json

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

def get_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
    })
    return session


def search_products(keyword: str, max_price: float = 2000, limit: int = 10) -> list:
    """
    Search Meesho for home decor products.
    Returns list of raw product dicts.
    """
    session = get_session()

    try:
        # Visit homepage first to get cookies
        session.get("https://www.meesho.com/", timeout=10)
        time.sleep(random.uniform(1.0, 2.5))

        search_url = f"https://www.meesho.com/search?q={keyword.replace(' ', '%20')}"
        response = session.get(search_url, timeout=20)
        soup = BeautifulSoup(response.text, "html.parser")

        # Try to find JSON data embedded in page (Next.js pattern)
        script_tags = soup.find_all("script", id="__NEXT_DATA__")
        if script_tags:
            try:
                data = json.loads(script_tags[0].string)
                # Navigate the Next.js data structure
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
                    products.append({
                        "title": item.get("name", item.get("title", "")),
                        "supplier": "Meesho",
                        "supplier_url": f"https://www.meesho.com/p/{item.get('slug', item.get('id', ''))}",
                        "supplier_price": price,
                        "images": image_urls[:3],
                        "rating": float(item.get("rating", {}).get("average", 4.0) if isinstance(item.get("rating"), dict) else item.get("rating", 4.0) or 4.0),
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
        session = get_session()
        response = session.get(supplier_url, headers=session.headers, timeout=10)
        page_text = response.text.lower()
        if "page not found" in page_text or "404" in page_text:
            return {"available": False, "in_stock": False}
        out_of_stock = "out of stock" in page_text or "sold out" in page_text
        return {"available": True, "in_stock": not out_of_stock}
    except Exception:
        return {"available": False, "in_stock": False}
