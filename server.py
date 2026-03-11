"""
server.py - FastAPI server for:
  - Product approve/reject/edit from email
  - Shopify order webhook receiver
Run: uvicorn server:app --host 0.0.0.0 --port 8000
"""

import hmac, hashlib, json
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import database
from integrations.shopify import list_product, get_product_url
from mailer.sender import send_order_email
from config import SHOPIFY_WEBHOOK_SECRET

app = FastAPI(title="Dropship AI Agent")


def page(title, message, color="#22c55e", icon="✅"):
    return f"""<html><head><title>{title}</title>
    <style>body{{font-family:Arial,sans-serif;display:flex;align-items:center;justify-content:center;
    height:100vh;margin:0;background:#f5f5f5}}
    .card{{background:white;border-radius:16px;padding:48px;text-align:center;
    box-shadow:0 4px 20px rgba(0,0,0,.1);max-width:480px}}
    .icon{{font-size:64px;margin-bottom:16px}}h1{{color:{color};margin:0 0 12px}}
    p{{color:#666;line-height:1.6}}a{{color:#ff6b35}}</style></head>
    <body><div class="card"><div class="icon">{icon}</div>
    <h1>{title}</h1><p>{message}</p></div></body></html>"""


# ─── APPROVE ────────────────────────────────────────────────
@app.get("/approve/{product_id}", response_class=HTMLResponse)
async def approve(product_id: str):
    product = database.get_product(product_id)
    if not product:
        return page("Not Found", "Product not found.", "#ef4444", "❌")
    if product["status"] != "pending":
        return page("Already Processed", f"This product is already <strong>{product['status']}</strong>.", "#f59e0b", "⚠️")

    shopify_id = list_product(product)
    if shopify_id:
        database.update_product_status(product_id, "listed", shopify_id)
        url = get_product_url(shopify_id)
        return page("Approved! 🎉",
            f"<strong>{product['title']}</strong> has been listed on Shopify as a draft.<br/><br/>"
            f'<a href="{url}" target="_blank">View on Shopify →</a>')
    return page("Shopify Error", "Product approved but Shopify listing failed. Check your API token.", "#ef4444", "❌")


# ─── REJECT ─────────────────────────────────────────────────
@app.get("/reject/{product_id}", response_class=HTMLResponse)
async def reject(product_id: str):
    product = database.get_product(product_id)
    if not product:
        return page("Not Found", "Product not found.", "#ef4444", "❌")
    if product["status"] != "pending":
        return page("Already Processed", f"Status: <strong>{product['status']}</strong>", "#f59e0b", "⚠️")
    database.update_product_status(product_id, "rejected")
    return page("Rejected", f"<strong>{product['title']}</strong> has been rejected.", "#64748b", "❌")


# ─── EDIT FORM ───────────────────────────────────────────────
@app.get("/edit/{product_id}", response_class=HTMLResponse)
async def edit_form(product_id: str):
    product = database.get_product(product_id)
    if not product:
        return page("Not Found", "Product not found.", "#ef4444", "❌")
    if product["status"] != "pending":
        return page("Already Processed", f"Status: <strong>{product['status']}</strong>", "#f59e0b", "⚠️")

    image = product["images"][0] if product.get("images") else ""
    img_html = f'<img src="{image}" style="width:100%;max-height:220px;object-fit:cover;border-radius:8px;margin-bottom:16px"/>' if image else ""

    return f"""<html><head><title>Edit Product</title>
    <style>
      body{{font-family:'Segoe UI',Arial,sans-serif;background:#f5f5f5;margin:0;padding:20px}}
      .card{{max-width:580px;margin:0 auto;background:white;border-radius:16px;padding:32px;box-shadow:0 4px 20px rgba(0,0,0,.1)}}
      h2{{color:#1a1a2e;margin:0 0 6px}}
      .sub{{color:#888;font-size:13px;margin-bottom:20px}}
      label{{display:block;font-size:12px;color:#888;font-weight:600;margin-bottom:4px;text-transform:uppercase}}
      input,textarea{{width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:8px;font-size:14px;
        box-sizing:border-box;margin-bottom:14px;font-family:inherit}}
      textarea{{height:120px;resize:vertical}}
      .btn-row{{display:flex;gap:10px;margin-top:6px}}
      .btn{{flex:1;padding:12px;border:none;border-radius:8px;font-size:15px;font-weight:700;cursor:pointer}}
      .btn-save{{background:#22c55e;color:white}}
      .btn-cancel{{background:#f1f5f9;color:#64748b}}
    </style></head>
    <body><div class="card">
      {img_html}
      <h2>✏️ Edit Product</h2>
      <p class="sub">Make your changes below, then click Save & Approve to list on Shopify.</p>
      <form method="POST" action="/edit/{product_id}">
        <label>Title</label>
        <input name="title" value="{product['title']}" required/>
        <label>Selling Price (₹)</label>
        <input name="price" type="number" step="0.01" value="{product.get('suggested_price',0)}" required/>
        <label>Description (HTML allowed)</label>
        <textarea name="description">{product.get('description','')}</textarea>
        <div class="btn-row">
          <button class="btn btn-save" type="submit">✅ Save & Approve</button>
          <a href="/reject/{product_id}" class="btn btn-cancel" style="text-align:center;text-decoration:none;display:block">❌ Reject</a>
        </div>
      </form>
    </div></body></html>"""


@app.post("/edit/{product_id}", response_class=HTMLResponse)
async def edit_submit(product_id: str, title: str = Form(...), price: float = Form(...), description: str = Form(...)):
    product = database.get_product(product_id)
    if not product:
        return page("Not Found", "Product not found.", "#ef4444", "❌")

    # Save edits
    database.update_product(product_id, {
        "title": title,
        "suggested_price": price,
        "description": description
    })

    # Fetch updated and list
    updated = database.get_product(product_id)
    shopify_id = list_product(updated)
    if shopify_id:
        database.update_product_status(product_id, "listed", shopify_id)
        url = get_product_url(shopify_id)
        return page("Saved & Listed! 🎉",
            f"<strong>{title}</strong> has been updated and listed on Shopify.<br/><br/>"
            f'<a href="{url}" target="_blank">View on Shopify →</a>')
    return page("Shopify Error", "Changes saved but Shopify listing failed.", "#ef4444", "❌")


# ─── ORDER WEBHOOK ───────────────────────────────────────────
@app.post("/webhook/order")
async def order_webhook(request: Request):
    body = await request.body()

    # Verify Shopify HMAC signature
    shopify_hmac = request.headers.get("X-Shopify-Hmac-Sha256", "")
    if SHOPIFY_WEBHOOK_SECRET and SHOPIFY_WEBHOOK_SECRET != "your_webhook_secret":
        digest = hmac.new(SHOPIFY_WEBHOOK_SECRET.encode(), body, hashlib.sha256).digest()
        import base64
        computed = base64.b64encode(digest).decode()
        if not hmac.compare_digest(computed, shopify_hmac):
            return {"status": "unauthorized"}

    try:
        order = json.loads(body)
        print(f"[Webhook] 🛍️ New order received: #{order.get('order_number')}")
        send_order_email(order)
        return {"status": "ok"}
    except Exception as e:
        print(f"[Webhook] Error: {e}")
        return {"status": "error"}


# ─── HEALTH CHECK ────────────────────────────────────────────
@app.get("/status")
async def status():
    pending = database.get_pending_products()
    return {"status": "running", "pending_approvals": len(pending)}
