
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Retailer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
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
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

class NotificationSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pushbullet_token = db.Column(db.String(200))
    enable = db.Column(db.Boolean, default=False)
