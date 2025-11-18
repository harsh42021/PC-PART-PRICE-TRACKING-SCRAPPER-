# backend/app.py
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
from psycopg2.extras import RealDictCursor

# Import local modules
# models.py contains SQLAlchemy models and helper functions (init_db etc)
from models import (
    db,
    Retailer,
    Build,
    Part,
    ProductUrl,
    PriceHistory,
    NotificationSettings,
    init_db as models_init_db,
)

# scraper and fx and pushbullet client
from scrapper import scrape_with_retailer
from fx import get_usd_to_cad_rate
from notifications.pushbullet import PushbulletClient

# create app, set static folder to React build
app = Flask(__name__, static_folder="../frontend/build", static_url_path="/")
CORS(app)

# Set up SQLite DB file inside instance folder (safe for Render)
app.instance_path = app.instance_path  # ensure attribute present
os.makedirs(app.instance_path, exist_ok=True)
DB_PATH = os.path.join(app.instance_path, "database.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# initialize db object
db.init_app(app)

@app.before_first_request
def initialize():
    # Create tables if missing
    with app.app_context():
        db.create_all()
        # Insert a default NotificationSettings row if none exists
        if NotificationSettings.query.first() is None:
            ns = NotificationSettings(enable=False, pushbullet_token="")
            db.session.add(ns)
            db.session.commit()
        # Insert a few builtin retailers if missing
        insert_builtin_retailers()

def insert_builtin_retailers():
    # Add common Canadian retailers if they do not exist
    builtins = [
        {"name":"CanadaComputers", "domain":"canadacomputers.com", "price_selector":None, "sold_by_selector":None, "sold_by_required":"canada computers", "default_currency":"CAD"},
        {"name":"MemoryExpress", "domain":"memoryexpress.com", "price_selector":None, "sold_by_selector":None, "sold_by_required":"memory express", "default_currency":"CAD"},
        {"name":"BestBuy", "domain":"bestbuy.ca", "price_selector":None, "sold_by_selector":None, "sold_by_required":"best buy", "default_currency":"CAD"},
        {"name":"Newegg", "domain":"newegg.ca", "price_selector":None, "sold_by_selector":None, "sold_by_required":"newegg", "default_currency":"CAD"},
        {"name":"Amazon.ca", "domain":"amazon.ca", "price_selector":None, "sold_by_selector":"#merchant-info", "sold_by_required":"amazon", "default_currency":"CAD"},
    ]
    for b in builtins:
        if Retailer.query.filter_by(name=b["name"]).first() is None:
            r = Retailer(
                name=b["name"],
                domain=b["domain"],
                price_selector=b["price_selector"],
                sold_by_selector=b["sold_by_selector"],
                sold_by_required=b["sold_by_required"],
                default_currency=b["default_currency"],
                active=True
            )
            db.session.add(r)
    db.session.commit()

# -----------------------
# Helper serialisers
# -----------------------
def retailer_to_dict(r):
    return {
        "id": r.id,
        "name": r.name,
        "domain": r.domain,
        "price_selector": r.price_selector,
        "sold_by_selector": r.sold_by_selector,
        "sold_by_required": r.sold_by_required,
        "default_currency": r.default_currency,
        "active": r.active,
    }

def build_to_dict(b):
    parts = Part.query.filter_by(build_id=b.id).all()
    return {
        "id": b.id,
        "name": b.name,
        "parts": [{"id": p.id, "category": p.category, "oem": p.oem, "label": p.label} for p in parts]
    }

# -----------------------
# API endpoints
# -----------------------

@app.route("/api/health", methods=["GET"])
def health():
    try:
        rate = get_usd_to_cad_rate()
    except Exception:
        rate = None
    settings = NotificationSettings.query.first()
    return jsonify({"status":"ok", "usd_to_cad": rate, "notifications_enabled": bool(settings.enable if settings else False)})

# RETAILERS
@app.route("/api/retailers", methods=["GET"])
def list_retailers():
    rows = Retailer.query.order_by(Retailer.active.desc(), Retailer.name).all()
    return jsonify([retailer_to_dict(r) for r in rows])

@app.route("/api/retailers", methods=["POST"])
def add_retailer():
    data = request.get_json() or {}
    name = data.get("name")
    if not name:
        return jsonify({"error":"name required"}), 400
    r = Retailer(
        name=name,
        domain=data.get("domain"),
        price_selector=data.get("price_selector"),
        sold_by_selector=data.get("sold_by_selector"),
        sold_by_required=data.get("sold_by_required"),
        default_currency=data.get("default_currency","CAD"),
        active=True
    )
    db.session.add(r)
    db.session.commit()
    return jsonify({"ok": True})

@app.route("/api/retailers/<int:rid>/toggle", methods=["POST"])
def toggle_retailer(rid):
    r = Retailer.query.get(rid)
    if not r:
        return jsonify({"error":"not found"}), 404
    r.active = not r.active
    db.session.commit()
    return jsonify({"ok": True})

# BUILDS
@app.route("/api/builds", methods=["GET"])
def get_builds():
    rows = Build.query.order_by(Build.id.desc()).all()
    return jsonify([build_to_dict(b) for b in rows])

@app.route("/api/builds", methods=["POST"])
def create_build():
    data = request.get_json() or {}
    name = data.get("name")
    if not name:
        return jsonify({"error":"name required"}), 400
    b = Build(name=name)
    db.session.add(b)
    db.session.commit()
    return jsonify({"ok": True})

@app.route("/api/builds/<int:bid>/parts", methods=["GET"])
def get_build_parts(bid):
    parts = Part.query.filter_by(build_id=bid).all()
    return jsonify([{"id":p.id,"category":p.category,"oem":p.oem,"label":p.label} for p in parts])

@app.route("/api/builds/<int:bid>/parts", methods=["POST"])
def add_build_part(bid):
    data = request.get_json() or {}
    category = data.get("category")
    oem = data.get("oem")
    label = data.get("label")
    if not category or not oem:
        return jsonify({"error":"category and oem required"}), 400
    p = Part(build_id=bid, category=category, oem=oem, label=label)
    db.session.add(p)
    db.session.commit()
    return jsonify({"ok": True})

@app.route("/api/builds/<int:bid>/parts", methods=["DELETE"])
def delete_build_part(bid):
    data = request.get_json() or {}
    category = data.get("category")
    oem = data.get("oem")
    if not category or not oem:
        return jsonify({"error":"category and oem required"}), 400
    Part.query.filter_by(build_id=bid, category=category, oem=oem).delete()
    db.session.commit()
    return jsonify({"ok": True})

# PRODUCT URLS
@app.route("/api/product_urls/<string:oem>", methods=["GET"])
def get_product_urls(oem):
    rows = ProductUrl.query.filter_by(oem=oem).all()
    result = []
    for r in rows:
        retailer = Retailer.query.get(r.retailer_id)
        result.append({
            "id": r.id,
            "oem": r.oem,
            "retailer_id": r.retailer_id,
            "retailer_name": retailer.name if retailer else None,
            "url": r.url,
            "created_at": None
        })
    return jsonify(result)

@app.route("/api/product_urls/<string:oem>", methods=["POST"])
def add_product_url(oem):
    data = request.get_json() or {}
    retailer_id = data.get("retailer_id")
    url = data.get("url")
    if not retailer_id or not url:
        return jsonify({"error":"retailer_id and url required"}), 400
    # upsert: if exists update
    existing = ProductUrl.query.filter_by(oem=oem, retailer_id=retailer_id).first()
    if existing:
        existing.url = url
    else:
        p = ProductUrl(oem=oem, retailer_id=retailer_id, url=url)
        db.session.add(p)
    db.session.commit()
    return jsonify({"ok": True})

@app.route("/api/product_urls/<int:uid>", methods=["DELETE"])
def delete_product_url(uid):
    ProductUrl.query.filter_by(id=uid).delete()
    db.session.commit()
    return jsonify({"ok": True})

# PRICE REFRESH (scrapes all active product URLs)
@app.route("/api/refresh", methods=["POST"])
def refresh_all():
    rows = ProductUrl.query.join(Retailer, ProductUrl.retailer_id==Retailer.id).filter(Retailer.active==True).all()
    settings = NotificationSettings.query.first()
    pb_key = settings.pushbullet_token if settings else None
    notifications_enabled = bool(settings.enable if settings else False)
    pb = PushbulletClient(api_key=pb_key)
    results = []
    for pu in rows:
        retailer = Retailer.query.get(pu.retailer_id)
        retailer_row = {
            "name": retailer.name,
            "domain": retailer.domain,
            "price_selector": retailer.price_selector,
            "sold_by_selector": retailer.sold_by_selector,
            "sold_by_required": retailer.sold_by_required,
            "default_currency": retailer.default_currency,
            "is_builtin": True if retailer.name.lower() in ["newegg","bestbuy","canadacomputers","memoryexpress","amazon.ca"] else False
        }
        try:
            out = scrape_with_retailer(pu.url, retailer_row)
        except Exception as e:
            results.append({"oem": pu.oem, "retailer": retailer.name, "error": str(e)})
            continue
        if out.get("error"):
            results.append({"oem": pu.oem, "retailer": retailer.name, "error": out.get("message")})
            continue
        price_cad = out.get("price_cad")
        price_raw = out.get("price_raw")
        original_currency = out.get("original_currency")
        ph = PriceHistory(oem=pu.oem, retailer_id=pu.retailer_id, price=price_cad, currency=original_currency, timestamp=datetime.utcnow())
        db.session.add(ph)
        db.session.commit()
        # check previous price
        prev = PriceHistory.query.filter_by(oem=pu.oem, retailer_id=pu.retailer_id).order_by(PriceHistory.timestamp.desc()).limit(2).all()
        previous_price = prev[1].price if len(prev) > 1 else None
        notify = False
        reason = None
        if previous_price is not None and price_cad is not None and price_cad < previous_price:
            notify = True
            reason = f"Price dropped from ${previous_price} to ${price_cad} CAD"
        if notify and notifications_enabled and pb_key:
            title = f"Price alert: {pu.oem}"
            body = f"{pu.oem} at {retailer.name}: ${price_cad} CAD. {reason}. {pu.url}"
            pb.send_note(title, body)
        results.append({"oem": pu.oem, "retailer": retailer.name, "price_cad": price_cad})
    return jsonify({"results": results})

# PRICE HISTORY
@app.route("/api/price_history/<string:oem>", methods=["GET"])
def price_history(oem):
    rows = PriceHistory.query.filter_by(oem=oem).order_by(PriceHistory.timestamp.desc()).limit(500).all()
    out = []
    for r in rows:
        retailer = Retailer.query.get(r.retailer_id)
        out.append({
            "id": r.id,
            "oem": r.oem,
            "retailer_name": retailer.name if retailer else None,
            "price": r.price,
            "currency": r.currency,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None
        })
    return jsonify(out)

# NOTIFICATION SETTINGS
@app.route("/api/notifications/settings", methods=["GET"])
def get_notifications_settings():
    s = NotificationSettings.query.first()
    if not s:
        return jsonify({"pushbullet_api_key": None, "notifications_enabled": False})
    return jsonify({"pushbullet_api_key": s.pushbullet_token, "notifications_enabled": bool(s.enable)})

@app.route("/api/notifications/settings", methods=["POST"])
def set_notifications_settings():
    data = request.get_json() or {}
    s = NotificationSettings.query.first()
    if not s:
        s = NotificationSettings()
        db.session.add(s)
    s.pushbullet_token = data.get("pushbullet_api_key", s.pushbullet_token)
    s.enable = bool(data.get("notifications_enabled", s.enable))
    db.session.commit()
    return jsonify({"ok": True})

# Serve frontend
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
