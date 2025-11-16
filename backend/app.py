# backend/app.py
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from db import init_db, insert_builtin_retailers_if_missing, get_conn, get_user_settings, upsert_user_settings
from scraper import scrape_with_retailer
from datetime import datetime
from psycopg2.extras import RealDictCursor
from notifications.pushbullet import PushbulletClient

# initialize DB and builtins
init_db()
insert_builtin_retailers_if_missing()

app = Flask(__name__, static_folder="../frontend/build", static_url_path="/")
CORS(app)

def query(sql, params=(), fetch=False, one=False):
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(sql, params)
    res = None
    if fetch:
        res = cur.fetchall()
    if one:
        res = cur.fetchone()
    conn.commit()
    cur.close(); conn.close()
    return res

@app.route("/api/health")
def health():
    settings = get_user_settings()
    from fx import get_usd_to_cad_rate
    return jsonify({"status":"ok","time":datetime.utcnow().isoformat(),"usd_to_cad": get_usd_to_cad_rate(), "notifications": bool(settings and settings.get("notifications_enabled"))})

# Retailers
@app.route("/api/retailers", methods=["GET"])
def list_retailers():
    rows = query("SELECT * FROM retailers ORDER BY is_builtin DESC, name", fetch=True)
    return jsonify(rows)

@app.route("/api/retailers", methods=["POST"])
def add_retailer():
    data = request.get_json() or {}
    name = data.get("name")
    domain = data.get("domain")
    price_selector = data.get("price_selector")
    sold_by_selector = data.get("sold_by_selector")
    sold_by_required = data.get("sold_by_required")
    if not name:
        return jsonify({"error":"name required"}), 400
    query("INSERT INTO retailers (name,domain,price_selector,sold_by_selector,sold_by_required,active,is_builtin) VALUES (%s,%s,%s,%s,%s,TRUE,FALSE)",
          (name,domain,price_selector,sold_by_selector,sold_by_required))
    return jsonify({"ok":True})

@app.route("/api/retailers/<int:rid>/toggle", methods=["POST"])
def toggle_retailer(rid):
    query("UPDATE retailers SET active = NOT active WHERE id=%s", (rid,))
    return jsonify({"ok":True})

# Builds and parts
@app.route("/api/builds", methods=["GET"])
def list_builds():
    rows = query("SELECT * FROM builds ORDER BY created_at DESC", fetch=True)
    return jsonify(rows)

@app.route("/api/builds", methods=["POST"])
def add_build():
    data = request.get_json() or {}
    name = data.get("name")
    if not name:
        return jsonify({"error":"name required"}), 400
    query("INSERT INTO builds (name) VALUES (%s)", (name,))
    return jsonify({"ok":True})

@app.route("/api/builds/<int:bid>/parts", methods=["GET"])
def get_build_parts(bid):
    rows = query("SELECT * FROM build_parts WHERE build_id=%s", (bid,), fetch=True)
    return jsonify(rows)

@app.route("/api/builds/<int:bid>/parts", methods=["POST"])
def add_build_part(bid):
    data = request.get_json() or {}
    category = data.get("category")
    oem = data.get("oem")
    label = data.get("label")
    if not category or not oem:
        return jsonify({"error":"category and oem required"}), 400
    query("INSERT INTO build_parts (build_id, category, oem, label) VALUES (%s,%s,%s,%s) ON CONFLICT (build_id, category, oem) DO NOTHING", (bid, category, oem, label))
    return jsonify({"ok":True})

@app.route("/api/builds/<int:bid>/parts", methods=["DELETE"])
def delete_build_part(bid):
    data = request.get_json() or {}
    category = data.get("category")
    oem = data.get("oem")
    if not category or not oem:
        return jsonify({"error":"category and oem required"}), 400
    query("DELETE FROM build_parts WHERE build_id=%s AND category=%s AND oem=%s", (bid, category, oem))
    return jsonify({"ok":True})

# Product URLs (per OEM per retailer)
@app.route("/api/product_urls/<string:oem>", methods=["GET"])
def get_product_urls(oem):
    rows = query("SELECT pu.*, r.name as retailer_name, r.domain as retailer_domain, r.active as retailer_active FROM product_urls pu JOIN retailers r ON pu.retailer_id=r.id WHERE pu.oem=%s", (oem,), fetch=True)
    return jsonify(rows)

@app.route("/api/product_urls/<string:oem>", methods=["POST"])
def add_product_url(oem):
    data = request.get_json() or {}
    retailer_id = data.get("retailer_id")
    url = data.get("url")
    if not retailer_id or not url:
        return jsonify({"error":"retailer_id and url required"}), 400
    query("INSERT INTO product_urls (oem, retailer_id, url) VALUES (%s,%s,%s) ON CONFLICT (oem, retailer_id) DO UPDATE SET url=EXCLUDED.url", (oem, retailer_id, url))
    return jsonify({"ok":True})

@app.route("/api/product_urls/<int:uid>", methods=["DELETE"])
def delete_product_url(uid):
    query("DELETE FROM product_urls WHERE id=%s", (uid,))
    return jsonify({"ok":True})

# Price refresh
@app.route("/api/refresh", methods=["POST"])
def refresh_all():
    conn = get_conn(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
      SELECT pu.id as pu_id, pu.oem, pu.retailer_id, pu.url,
             r.name as retailer_name, r.domain, r.price_selector, r.sold_by_selector, r.sold_by_required, r.active, r.is_builtin
      FROM product_urls pu
      JOIN retailers r ON pu.retailer_id = r.id
      WHERE r.active = TRUE
    """)
    rows = cur.fetchall()
    settings = get_user_settings()
    pb_key = settings.get("pushbullet_api_key") if settings else None
    notifications_enabled = bool(settings and settings.get("notifications_enabled"))
    pb = PushbulletClient(api_key=pb_key)
    results = []
    for r in rows:
        retailer_row = {k: r.get(k) for k in ["name","domain","price_selector","sold_by_selector","sold_by_required","is_builtin"]}
        retailer_row["name"] = r["retailer_name"]
        try:
            out = scrape_with_retailer(r["url"], retailer_row)
        except Exception as e:
            out = {"error": True, "message": str(e)}
        if out.get("error"):
            results.append({"oem": r["oem"], "retailer_id": r["retailer_id"], "error": out.get("message")})
            continue
        price_cad = out.get("price_cad")
        price_raw = out.get("price_raw")
        original_currency = out.get("original_currency")
        # add to price_history
        cur2 = conn.cursor()
        cur2.execute("INSERT INTO price_history (oem, retailer_id, price_raw, original_currency, price_cad, checked_at) VALUES (%s,%s,%s,%s,%s,NOW())",
                     (r["oem"], r["retailer_id"], price_raw, original_currency, price_cad))
        conn.commit()
        # check previous
        cur2.execute("SELECT price_cad FROM price_history WHERE oem=%s AND retailer_id=%s ORDER BY checked_at DESC LIMIT 2", (r["oem"], r["retailer_id"]))
        hist = cur2.fetchall()
        previous = hist[1]["price_cad"] if len(hist) > 1 else None
        cur2.execute("SELECT * FROM notification_rules WHERE oem=%s AND enabled=TRUE", (r["oem"],))
        rules = cur2.fetchall()
        notify = False
        reason = None
        if previous is not None and price_cad is not None and price_cad < previous:
            notify = True
            reason = f"Price dropped from ${previous} to ${price_cad} CAD"
        for rule in rules:
            thresh = rule.get("threshold_price_cad")
            if thresh is not None and price_cad is not None and price_cad <= float(thresh):
                notify = True
                reason = f"Price ${price_cad} <= threshold ${thresh}"
        if notify and notifications_enabled and pb_key:
            title = f"Price alert: {r['oem']}"
            body = f"{r['oem']} at {r['retailer_name']}: ${price_cad} CAD. {reason}. {r['url']}"
            pb.send_note(title, body)
        cur2.close()
        results.append({"oem": r["oem"], "retailer_id": r["retailer_id"], "price_cad": price_cad})
    cur.close(); conn.close()
    return jsonify({"results": results})

@app.route("/api/price_history/<string:oem>", methods=["GET"])
def price_history(oem):
    rows = query("SELECT ph.*, r.name as retailer_name FROM price_history ph JOIN retailers r ON ph.retailer_id=r.id WHERE ph.oem=%s ORDER BY checked_at DESC LIMIT 500", (oem,), fetch=True)
    return jsonify(rows)

# Notifications settings
@app.route("/api/notifications/settings", methods=["GET"])
def get_notifications_settings():
    settings = get_user_settings()
    if not settings:
        return jsonify({"pushbullet_api_key": None, "notifications_enabled": True})
    return jsonify({"pushbullet_api_key": settings.get("pushbullet_api_key"), "notifications_enabled": bool(settings.get("notifications_enabled"))})

@app.route("/api/notifications/settings", methods=["POST"])
def set_notifications_settings():
    data = request.get_json() or {}
    key = data.get("pushbullet_api_key")
    enabled = data.get("notifications_enabled")
    upsert_user_settings(pushbullet_api_key=key, notifications_enabled=enabled)
    return jsonify({"ok":True})

# Serve frontend
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path != "" and os.path.exists(app.static_folder + "/" + path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
