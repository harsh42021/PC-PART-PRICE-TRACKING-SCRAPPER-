import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.orm import relationship

db = SQLAlchemy()

########################################
# DATABASE MODELS
########################################

class Retailer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    domain = db.Column(db.String(200))
    price_selector = db.Column(db.String(200))
    sold_by_selector = db.Column(db.String(200))
    sold_by_required = db.Column(db.String(200))
    default_currency = db.Column(db.String(10), default="CAD")
    active = db.Column(db.Boolean, default=True)


class Build(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))


class Part(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    build_id = db.Column(db.Integer, db.ForeignKey('build.id'))
    category = db.Column(db.String(50))
    oem = db.Column(db.String(50))
    label = db.Column(db.String(100), nullable=True)


class ProductUrl(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    oem = db.Column(db.String(50))
    retailer_id = db.Column(db.Integer, db.ForeignKey('retailer.id'))
    url = db.Column(db.String(500))


class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    oem = db.Column(db.String(50))
    retailer_id = db.Column(db.Integer, db.ForeignKey('retailer.id'))
    price = db.Column(db.Float)
    currency = db.Column(db.String(10))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class NotificationSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pushbullet_token = db.Column(db.String(200))
    enable = db.Column(db.Boolean, default=False)


########################################
# INIT DB
########################################

def init_db():
    """Initialize database file and tables."""
    from flask import current_app
    db_path = os.path.join(current_app.instance_path, "database.db")

    # Ensure instance folder exists
    os.makedirs(current_app.instance_path, exist_ok=True)

    current_app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    current_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(current_app)

    with current_app.app_context():
        db.create_all()


########################################
# RETAILER FUNCTIONS
########################################

def get_retailers():
    rows = Retailer.query.all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "domain": r.domain,
            "price_selector": r.price_selector,
            "sold_by_selector": r.sold_by_selector,
            "sold_by_required": r.sold_by_required,
            "default_currency": r.default_currency,
            "active": r.active,
        }
        for r in rows
    ]


def add_retailer(data):
    r = Retailer(
        name=data.get("name"),
        domain=data.get("domain"),
        price_selector=data.get("price_selector"),
        sold_by_selector=data.get("sold_by_selector"),
        sold_by_required=data.get("sold_by_required"),
        default_currency=data.get("default_currency", "CAD"),
        active=True,
    )
    db.session.add(r)
    db.session.commit()


def delete_retailer(retailer_id):
    Retailer.query.filter_by(id=retailer_id).delete()
    db.session.commit()



########################################
# BUILD FUNCTIONS
########################################

def get_all_builds():
    rows = Build.query.all()
    result = []
    for b in rows:
        parts = Part.query.filter_by(build_id=b.id).all()
        result.append({
            "id": b.id,
            "name": b.name,
            "parts": [
                {
                    "id": p.id,
                    "category": p.category,
                    "oem": p.oem,
                    "label": p.label,
                }
                for p in parts
            ]
        })
    return result


def add_build(data):
    b = Build(name=data.get("name"))
    db.session.add(b)
    db.session.commit()


def delete_build(build_id):
    Part.query.filter_by(build_id=build_id).delete()
    Build.query.filter_by(id=build_id).delete()
    db.session.commit()


########################################
# NOTIFICATION SETTINGS
########################################

def get_notification_settings():
    row = NotificationSettings.query.first()
    if not row:
        return {"enable": False, "pushbullet_token": ""}
    return {"enable": row.enable, "pushbullet_token": row.pushbullet_token}


def update_notification_settings(data):
    row = NotificationSettings.query.first()
    if not row:
        row = NotificationSettings()
        db.session.add(row)
    row.enable = data.get("enable", False)
    row.pushbullet_token = data.get("pushbullet_token", "")
    db.session.commit()
