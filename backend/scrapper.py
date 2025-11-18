# backend/scraper.py (fixed and complete)
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from fx import get_usd_to_cad_rate

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PCPartPriceTracker/1.0)"}

def _extract_number(s):
    if not s:
        return None
    cleaned = re.sub(r"[^\d\.\,]", "", s)
    cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except:
        return None

def detect_currency(price_text):
    if not price_text:
        return None
    t = price_text.upper()
    if "CA$" in t or "CAD" in t:
        return "CAD"
    if "US$" in t or "USD" in t:
        return "USD"
    # ambiguous "$" — unknown
    if t.strip().startswith("$"):
        return None
    return None

def normalize_price_to_cad(price_text, retailer_default_currency="CAD"):
    if not price_text:
        return (None, None, None)
    detected = detect_currency(price_text)
    num = _extract_number(price_text)
    if num is None:
        return (None, detected, None)
    if detected == "USD":
        rate = get_usd_to_cad_rate()
        return (round(num * rate, 2), "USD", num)
    if detected == "CAD":
        return (round(num, 2), "CAD", num)
    # fallback: retailer default
    if retailer_default_currency and retailer_default_currency.upper() == "USD":
        rate = get_usd_to_cad_rate()
        return (round(num * rate, 2), "USD(default)", num)
    return (round(num, 2), "CAD(assumed)", num)


# Built-in scrapers: each returns dict or raises
def _scrape_canadacomputers(url):
    r = requests.get(url, headers=HEADERS, timeout=15); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    price_raw = None
    for sel in ["span[itemprop='price']", ".price", ".product-price span", ".price-big"]:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            price_raw = el.get_text(" ", strip=True); break
    if not price_raw:
        txt = soup.find(string=re.compile(r"\$\s*\d"))
        if txt: price_raw = txt.strip()
    seller_el = soup.find(string=re.compile(r"(Sold by|Ships from|Seller|Sold & shipped)", re.I))
    seller_text = seller_el.strip() if seller_el else None
    availability = None
    if soup.find(string=re.compile(r"Out of Stock", re.I)): availability = "Out of Stock"
    elif soup.find(string=re.compile(r"In stock|Available", re.I)): availability = "In Stock"
    price_cad, curr, raw_num = normalize_price_to_cad(price_raw)
    return {"price_raw": price_raw, "seller_text": seller_text, "price_cad": price_cad, "original_currency": curr, "availability": availability, "timestamp": datetime.utcnow().isoformat()}

def _scrape_memoryexpress(url):
    r = requests.get(url, headers=HEADERS, timeout=15); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    price_raw = None
    og = soup.select_one("meta[property='og:price:amount']")
    if og and og.get("content"): price_raw = og.get("content")
    if not price_raw:
        for sel in [".product-price .price", ".price", "span[itemprop='price']"]:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                price_raw = el.get_text(" ", strip=True); break
    seller_el = soup.find(string=re.compile(r"(Sold by|Ships from|Seller|Sold & shipped)", re.I))
    seller_text = seller_el.strip() if seller_el else None
    availability = None
    if soup.find(string=re.compile(r"Out of Stock", re.I)): availability = "Out of Stock"
    elif soup.find(string=re.compile(r"In Stock|Available", re.I)): availability = "In Stock"
    price_cad, curr, raw_num = normalize_price_to_cad(price_raw)
    return {"price_raw": price_raw, "seller_text": seller_text, "price_cad": price_cad, "original_currency": curr, "availability": availability, "timestamp": datetime.utcnow().isoformat()}

def _scrape_bestbuy(url):
    r = requests.get(url, headers=HEADERS, timeout=15); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    price_raw = None
    for sel in [".pricing-price .sr-only", ".priceView-customer-price span", ".priceBlock"]:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            price_raw = el.get_text(" ", strip=True); break
    if not price_raw:
        txt = soup.find(string=re.compile(r"\$\s*\d"))
        if txt: price_raw = txt.strip()
    seller_el = soup.select_one(".fulfillment-fulfillment-details, .seller-info, .productSellerContainer")
    seller_text = seller_el.get_text(" ", strip=True) if seller_el else None
    availability = None
    if soup.find(string=re.compile(r"Out of Stock", re.I)): availability = "Out of Stock"
    elif soup.find(string=re.compile(r"In stock|Available", re.I)): availability = "In Stock"
    price_cad, curr, raw_num = normalize_price_to_cad(price_raw)
    return {"price_raw": price_raw, "seller_text": seller_text, "price_cad": price_cad, "original_currency": curr, "availability": availability, "timestamp": datetime.utcnow().isoformat()}

def _scrape_newegg(url):
    r = requests.get(url, headers=HEADERS, timeout=15); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    price_raw = None
    for sel in [".price-current", ".product-price .price", ".priceView-hero-price span"]:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            price_raw = el.get_text(" ", strip=True); break
    if not price_raw:
        txt = soup.find(string=re.compile(r"\$\s*\d"))
        if txt: price_raw = txt.strip()
    seller_el = soup.find(string=re.compile(r"(Sold by|Ships from|Seller|Sold & shipped|Marketplace)", re.I))
    seller_text = seller_el.strip() if seller_el else None
    availability = None
    if soup.find(string=re.compile(r"Out of Stock", re.I)): availability = "Out of Stock"
    elif soup.find(string=re.compile(r"In stock|Available", re.I)): availability = "In Stock"
    price_cad, curr, raw_num = normalize_price_to_cad(price_raw)
    return {"price_raw": price_raw, "seller_text": seller_text, "price_cad": price_cad, "original_currency": curr, "availability": availability, "timestamp": datetime.utcnow().isoformat()}

def _scrape_amazon(url):
    r = requests.get(url, headers=HEADERS, timeout=15); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    price_raw = None
    for sel in ["#priceblock_ourprice", "#priceblock_dealprice", ".a-price .a-offscreen"]:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            price_raw = el.get_text(" ", strip=True); break
    seller_el = soup.select_one("#merchant-info") or soup.find(string=re.compile(r"(Sold by|Ships from|Seller)", re.I))
    seller_text = seller_el.get_text(" ", strip=True) if hasattr(seller_el, "get_text") else (seller_el.strip() if seller_el else None)
    availability = None
    if soup.find(string=re.compile(r"Currently unavailable|Out of Stock", re.I)): availability = "Out of Stock"
    elif soup.find(string=re.compile(r"In stock|Available", re.I)): availability = "In Stock"
    price_cad, curr, raw_num = normalize_price_to_cad(price_raw)
    return {"price_raw": price_raw, "seller_text": seller_text, "price_cad": price_cad, "original_currency": curr, "availability": availability, "timestamp": datetime.utcnow().isoformat()}

BUILTINS = {
    "canadacomputers": _scrape_canadacomputers,
    "memoryexpress": _scrape_memoryexpress,
    "bestbuy": _scrape_bestbuy,
    "newegg": _scrape_newegg,
    "amazon": _scrape_amazon
}

def scrape_with_retailer(url, retailer_row):
    """
    Scrape a URL using built-in logic for known retailers or a simple fallback for custom retailers.
    retailer_row is a dict with keys: name, domain, price_selector, sold_by_selector, sold_by_required, default_currency
    """
    name = (retailer_row.get("name") or "").lower()
    domain = (retailer_row.get("domain") or "").lower()
    for frag, fn in BUILTINS.items():
        if frag in name or (domain and frag in domain):
            try:
                res = fn(url)
            except Exception as e:
                return {"error": True, "message": str(e)}
            sold_req = (retailer_row.get("sold_by_required") or "").strip().lower()
            seller_text = (res.get("seller_text") or "").lower() if res.get("seller_text") else ""
            if sold_req and sold_req not in seller_text:
                return {"error": True, "message": "Listing not sold & shipped by retailer (marketplace or third-party)."}
            return res
    # custom retailer fallback: try to find price and optionally sold_by info using selectors
    try:
        r = requests.get(url, headers=HEADERS, timeout=15); r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        price_text = None
        ps = retailer_row.get("price_selector")
        if ps:
            el = soup.select_one(ps)
            if el:
                price_text = el.get_text(" ", strip=True)
        if not price_text:
            txt = soup.find(string=re.compile(r"\$\s*\d"))
            if txt: price_text = txt.strip()
        sold_by_text = None
        ssel = retailer_row.get("sold_by_selector")
        if ssel:
            sel = soup.select_one(ssel)
            if sel:
                sold_by_text = sel.get_text(" ", strip=True)
        sold_req = (retailer_row.get("sold_by_required") or "").strip().lower()
        if sold_req:
            if not sold_by_text or sold_req not in sold_by_text.lower():
                return {"error": True, "message": "Listing not sold & shipped by retailer (marketplace or third-party)."}
        price_cad, curr, raw_num = normalize_price_to_cad(price_text, retailer_default_currency=retailer_row.get("default_currency","CAD"))
        availability = None
        if soup.find(string=re.compile(r"Out of Stock", re.I)): availability = "Out of Stock"
        elif soup.find(string=re.compile(r"In stock|Available", re.I)): availability = "In Stock"
        return {"price_raw": price_text, "seller_text": sold_by_text, "price_cad": price_cad, "original_currency": curr, "availability": availability, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        return {"error": True, "message": str(e)}
