"""
email/sender.py - Sends product approval emails and order notification emails
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER, SERVER_BASE_URL


def _send_email(subject: str, html_body: str) -> bool:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.attach(MIMEText(html_body, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        return True
    except Exception as e:
        print(f"[Email] Error: {e}")
        return False


def build_product_card(product: dict) -> str:
    pid = product["id"]
    image = product["images"][0] if product.get("images") else "https://via.placeholder.com/680x210?text=No+Image"
    tags_html = "".join([f'<span style="background:#f0f0f0;border-radius:4px;padding:2px 7px;font-size:11px;margin:2px;display:inline-block">{t}</span>' for t in product.get("tags", [])[:5]])
    approve_url = f"{SERVER_BASE_URL}/approve/{pid}"
    reject_url = f"{SERVER_BASE_URL}/reject/{pid}"
    edit_url = f"{SERVER_BASE_URL}/edit/{pid}"

    return f"""
    <div style="background:white;border-radius:12px;margin:16px 0;box-shadow:0 2px 10px rgba(0,0,0,.07);overflow:hidden">
      <img src="{image}" style="width:100%;height:210px;object-fit:cover;background:#eee" alt="{product['title']}"/>
      <div style="padding:20px">
        <div style="display:inline-block;background:#ff6b35;color:white;font-size:11px;font-weight:700;padding:3px 10px;border-radius:20px;margin-bottom:8px">⭐ Score: {product.get('score',0)}/10</div>
        <div style="font-size:18px;font-weight:700;margin:0 0 4px;color:#1a1a2e">{product['title']}</div>
        <div style="font-size:12px;color:#888;font-style:italic;margin-bottom:12px">{product.get('score_reason','')}</div>

        <div style="display:flex;gap:10px;margin:12px 0;flex-wrap:wrap">
          <div style="background:#fff8f5;border:1px solid #ffe0d0;border-radius:8px;padding:8px 12px;text-align:center;flex:1;min-width:75px">
            <div style="font-size:10px;color:#aaa;text-transform:uppercase">Supplier Price</div>
            <div style="font-size:15px;font-weight:700;color:#ff6b35">₹{product.get('supplier_price',0):.0f}</div>
          </div>
          <div style="background:#fff8f5;border:1px solid #ffe0d0;border-radius:8px;padding:8px 12px;text-align:center;flex:1;min-width:75px">
            <div style="font-size:10px;color:#aaa;text-transform:uppercase">Sell Price</div>
            <div style="font-size:15px;font-weight:700;color:#ff6b35">₹{product.get('suggested_price',0):.0f}</div>
          </div>
          <div style="background:#fff8f5;border:1px solid #ffe0d0;border-radius:8px;padding:8px 12px;text-align:center;flex:1;min-width:75px">
            <div style="font-size:10px;color:#aaa;text-transform:uppercase">Margin</div>
            <div style="font-size:15px;font-weight:700;color:#ff6b35">{product.get('profit_margin',0)}%</div>
          </div>
          <div style="background:#fff8f5;border:1px solid #ffe0d0;border-radius:8px;padding:8px 12px;text-align:center;flex:1;min-width:75px">
            <div style="font-size:10px;color:#aaa;text-transform:uppercase">Source</div>
            <div style="font-size:12px;font-weight:700;color:#ff6b35">{product.get('supplier','')}</div>
          </div>
        </div>

        <div style="font-size:13px;color:#555;line-height:1.6;margin:12px 0">{product.get('description','')}</div>
        <div style="margin:10px 0">{tags_html}</div>

        <div style="display:flex;gap:10px;margin-top:14px">
          <a href="{approve_url}" style="flex:1;padding:11px;border-radius:8px;text-align:center;font-weight:700;font-size:14px;text-decoration:none;display:block;background:#22c55e;color:white">✅ Approve & List</a>
          <a href="{edit_url}" style="flex:1;padding:11px;border-radius:8px;text-align:center;font-weight:700;font-size:14px;text-decoration:none;display:block;background:#3b82f6;color:white">✏️ Edit & Approve</a>
          <a href="{reject_url}" style="flex:1;padding:11px;border-radius:8px;text-align:center;font-weight:700;font-size:14px;text-decoration:none;display:block;background:#f1f5f9;color:#64748b;border:1px solid #e2e8f0">❌ Reject</a>
        </div>
        <div style="font-size:11px;color:#bbb;text-align:center;margin-top:8px">
          <a href="{product.get('supplier_url','#')}" style="color:#ff6b35">View on {product.get('supplier','Supplier')}</a>
        </div>
      </div>
    </div>
    """


def send_approval_email(products: list) -> bool:
    if not products:
        return False

    with open("email/templates/product_email.html") as f:
        template = f.read()

    cards = "".join([build_product_card(p) for p in products])
    html = template.replace("{{product_count}}", str(len(products)))
    html = html.replace("{{date}}", datetime.now().strftime("%B %d, %Y"))
    html = html.replace("{{product_cards}}", cards)

    sent = _send_email(
        f"🛒 {len(products)} New Home Decor Products Need Your Approval",
        html
    )
    if sent:
        print(f"[Email] ✅ Approval email sent with {len(products)} products")
    return sent


def send_order_email(order: dict) -> bool:
    """Send order notification email to owner."""
    try:
        with open("email/templates/order_email.html") as f:
            template = f.read()
    except FileNotFoundError:
        template = "<html><body>{{content}}</body></html>"

    shipping = order.get("shipping_address", {})
    customer = order.get("customer", {})

    # Build order items rows
    items_html = ""
    for item in order.get("line_items", []):
        items_html += f"""<tr>
          <td>{item.get('name','')}</td>
          <td>{item.get('quantity',1)}</td>
          <td>₹{item.get('price','0')}</td>
        </tr>"""

    # Customer note
    note = order.get("note", "")
    note_section = ""
    if note:
        note_section = f"""<div class="section">
          <h3>💬 Customer Note / Special Request</h3>
          <div class="note-box">{note}</div>
        </div>"""

    html = template
    html = html.replace("{{order_number}}", str(order.get("order_number", "")))
    html = html.replace("{{order_date}}", datetime.now().strftime("%B %d, %Y %I:%M %p"))
    html = html.replace("{{customer_name}}", f"{customer.get('first_name','')} {customer.get('last_name','')}".strip())
    html = html.replace("{{customer_email}}", customer.get("email", "N/A"))
    html = html.replace("{{customer_phone}}", shipping.get("phone", customer.get("phone", "N/A")))
    html = html.replace("{{shipping_address}}", shipping.get("address1", "") + " " + shipping.get("address2", ""))
    html = html.replace("{{shipping_city}}", shipping.get("city", ""))
    html = html.replace("{{shipping_state}}", shipping.get("province", ""))
    html = html.replace("{{shipping_zip}}", shipping.get("zip", ""))
    html = html.replace("{{order_items}}", items_html)
    html = html.replace("{{order_total}}", f"₹{order.get('total_price','0')}")
    html = html.replace("{{customer_note_section}}", note_section)

    sent = _send_email(
        f"🛍️ New Order #{order.get('order_number','')} — Action Required",
        html
    )
    if sent:
        print(f"[Email] ✅ Order notification sent for order #{order.get('order_number','')}")
    return sent
