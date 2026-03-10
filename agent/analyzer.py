"""
agent/analyzer.py - AI-powered product analysis using FREE Google Gemini API
Scores products and generates SEO-optimized descriptions (NO return/refund policy)
"""

import requests
import json
import re
from config import GEMINI_API_KEY, MIN_PROFIT_MARGIN

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
)


def call_gemini(prompt: str) -> str:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1000}
    }
    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
            json=payload, timeout=20
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"[Gemini] Error: {e}")
        return ""


def calculate_suggested_price(supplier_price: float) -> float:
    return round(supplier_price * 2.5, 2)


def calculate_profit_margin(supplier_price: float, retail_price: float) -> float:
    if retail_price == 0:
        return 0
    return round(((retail_price - supplier_price) / retail_price) * 100, 1)


def analyze_product(product: dict):
    supplier_price = product.get("supplier_price", 0)
    suggested_price = calculate_suggested_price(supplier_price)
    margin = calculate_profit_margin(supplier_price, suggested_price)

    if margin < MIN_PROFIT_MARGIN:
        return None

    prompt = f"""You are an expert dropshipping analyst for an Indian home decor Shopify store.
Analyze this product. Respond ONLY with a valid JSON object, no markdown, no backticks.

Product:
- Title: {product.get('title')}
- Supplier: {product.get('supplier')}
- Supplier Price: Rs.{supplier_price}
- Suggested Retail Price: Rs.{suggested_price}
- Rating: {product.get('rating', 'N/A')}

STRICT RULES for description:
- Highlight product beauty, quality, home decor appeal
- Mention ships within India
- DO NOT mention return policy, replacement policy, refund, or warranty

Return this JSON:
{{
  "score": <float 1-10>,
  "score_reason": "<one sentence>",
  "seo_title": "<compelling title under 70 chars>",
  "description": "<HTML 3-4 sentences, no return/refund mention>",
  "tags": ["tag1","tag2","tag3","tag4","tag5"],
  "pass": <true if score >= 6>
}}"""

    text = call_gemini(prompt)
    if not text:
        return None

    try:
        clean = text.strip()
        json_match = re.search(r'\{.*\}', clean, re.DOTALL)
        if json_match:
            clean = json_match.group()
        analysis = json.loads(clean)

        if not analysis.get("pass"):
            return None

        product["title"] = analysis.get("seo_title", product["title"])
        product["description"] = analysis.get("description", "")
        product["tags"] = analysis.get("tags", [])
        product["score"] = analysis.get("score", 5.0)
        product["score_reason"] = analysis.get("score_reason", "")
        product["suggested_price"] = suggested_price
        product["profit_margin"] = margin
        return product

    except Exception as e:
        print(f"[Analyzer] Parse error for '{product.get('title')}': {e}")
        return None
