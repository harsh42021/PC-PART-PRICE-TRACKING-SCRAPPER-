# backend/db.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Please set DATABASE_URL environment variable (Postgres)")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # retailers
    cur.execute("""
    CREATE TABLE IF NOT EXISTS retailers (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        domain TEXT,
        price_selector TEXT,
        sold_by_selector TEXT,
        sold_by_required TEXT,
        active BOOLEAN DEFAULT TRUE,
        is_builtin BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """)
    # products
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        oem VARCHAR(255) NOT NULL,
        label TEXT,
        category VARCHAR(80) NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """)
    # builds (unlimited)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS builds (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """)
    # build_parts: map build -> category -> multiple part numbers
    cur.execute("""
    CREATE TABLE IF NOT EXISTS build_parts (
        id SERIAL PRIMARY KEY,
        build_id INTEGER REFERENCES builds(id) ON DELETE CASCADE,
        category TEXT NOT NULL,
        oem VARCHAR(255) NOT NULL,
        label TEXT,
        UNIQUE(build_id, category, oem)
    );
    """)
    # product_urls (product per retailer)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS product_urls (
        id SERIAL PRIMARY KEY,
        oem VARCHAR(255) NOT NULL,
        retailer_id INTEGER REFERENCES retailers(id) ON DELETE CASCADE,
        url TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(oem, retailer_id)
    );
    """)
    # price_history
    cur.execute("""
    CREATE TABLE IF NOT EXISTS price_history (
        id SERIAL PRIMARY KEY,
        oem VARCHAR(255) NOT NULL,
        retailer_id INTEGER REFERENCES retailers(id) ON DELETE CASCADE,
        price_raw TEXT,
        original_currency VARCHAR(20),
        price_cad DOUBLE PRECISION,
        checked_at TIMESTAMP DEFAULT NOW()
    );
    """)
    # user settings
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_settings (
        id SERIAL PRIMARY KEY,
        pushbullet_api_key TEXT,
        notifications_enabled BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """)
    # notification rules
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notification_rules (
        id SERIAL PRIMARY KEY,
        oem VARCHAR(255),
        threshold_price_cad DOUBLE PRECISION,
        enabled BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def insert_builtin_retailers_if_missing():
    conn = get_conn()
    cur = conn.cursor()
    builtins = [
        ("CanadaComputers", "canadacomputers.com", None, None, "canada computers", True),
        ("MemoryExpress", "memoryexpress.com", None, None, "memory express", True),
        ("BestBuy", "bestbuy.ca", None, None, "best buy", True),
        ("Newegg", "newegg.ca", None, None, "newegg", True),
        ("Amazon.ca", "amazon.ca", None, "#merchant-info", "amazon", True)
    ]
    for name, domain, price_sel, sold_sel, sold_required, is_builtin in builtins:
        cur.execute("SELECT id FROM retailers WHERE name=%s", (name,))
        if cur.fetchone() is None:
            cur.execute("""
            INSERT INTO retailers (name, domain, price_selector, sold_by_selector, sold_by_required, active, is_builtin)
            VALUES (%s,%s,%s,%s,%s,TRUE,%s)
            """, (name, domain, price_sel, sold_sel, sold_required, is_builtin))
    conn.commit()
    cur.close()
    conn.close()

def get_user_settings():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM user_settings ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def upsert_user_settings(pushbullet_api_key=None, notifications_enabled=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM user_settings LIMIT 1")
    if cur.fetchone() is None:
        cur.execute("INSERT INTO user_settings (pushbullet_api_key, notifications_enabled) VALUES (%s,%s)",
                    (pushbullet_api_key, notifications_enabled if notifications_enabled is not None else True))
    else:
        if pushbullet_api_key is not None:
            cur.execute("UPDATE user_settings SET pushbullet_api_key=%s", (pushbullet_api_key,))
        if notifications_enabled is not None:
            cur.execute("UPDATE user_settings SET notifications_enabled=%s", (notifications_enabled,))
    conn.commit()
    cur.close(); conn.close()
