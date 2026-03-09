"""
database.py - Stores products, tracks status, and prevents duplicates
"""

import sqlite3
import json
import uuid
from datetime import datetime

DB_PATH = "dropship_agent.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            title_lower TEXT,
            description TEXT,
            supplier TEXT,
            supplier_url TEXT,
            supplier_price REAL,
            suggested_price REAL,
            profit_margin REAL,
            score REAL,
            images TEXT,
            tags TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            updated_at TEXT,
            shopify_product_id TEXT
        )
    """)
    conn.commit()
    conn.close()


def product_exists(title: str, supplier_url: str) -> bool:
    """Check if product already exists by title or URL."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id FROM products WHERE title_lower = ? OR supplier_url = ?",
        (title.strip().lower(), supplier_url)
    )
    row = c.fetchone()
    conn.close()
    return row is not None


def save_product(product: dict) -> str:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    product_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    c.execute("""
        INSERT INTO products (
            id, title, title_lower, description, supplier, supplier_url,
            supplier_price, suggested_price, profit_margin, score,
            images, tags, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
    """, (
        product_id,
        product.get("title"),
        product.get("title", "").strip().lower(),
        product.get("description"),
        product.get("supplier"),
        product.get("supplier_url"),
        product.get("supplier_price"),
        product.get("suggested_price"),
        product.get("profit_margin"),
        product.get("score"),
        json.dumps(product.get("images", [])),
        json.dumps(product.get("tags", [])),
        now, now
    ))
    conn.commit()
    conn.close()
    return product_id


def get_product(product_id: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = c.fetchone()
    conn.close()
    if row:
        p = dict(row)
        p["images"] = json.loads(p["images"] or "[]")
        p["tags"] = json.loads(p["tags"] or "[]")
        return p
    return None


def get_pending_products() -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE status = 'pending' ORDER BY score DESC")
    rows = c.fetchall()
    conn.close()
    products = []
    for row in rows:
        p = dict(row)
        p["images"] = json.loads(p["images"] or "[]")
        p["tags"] = json.loads(p["tags"] or "[]")
        products.append(p)
    return products


def update_product(product_id: str, updates: dict):
    """Update product fields (price, title, description, status, shopify_id)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    allowed = ["title", "description", "suggested_price", "status", "shopify_product_id"]
    fields = {k: v for k, v in updates.items() if k in allowed}
    fields["updated_at"] = now
    set_clause = ", ".join([f"{k} = ?" for k in fields])
    values = list(fields.values()) + [product_id]
    c.execute(f"UPDATE products SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def update_product_status(product_id: str, status: str, shopify_id: str = None):
    update_product(product_id, {"status": status, "shopify_product_id": shopify_id or ""})


def get_listed_products_older_than(days: int) -> list:
    """Get agent-listed products older than N days."""
    from datetime import timedelta
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        "SELECT * FROM products WHERE status = 'listed' AND created_at < ?",
        (cutoff,)
    )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]
