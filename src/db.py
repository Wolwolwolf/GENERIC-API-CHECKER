import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "generics.db"
CONFIG_DIR = BASE_DIR / "config"

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    country TEXT NOT NULL,
    authority TEXT NOT NULL,
    product_name TEXT NOT NULL,
    api_en TEXT NOT NULL,
    api_zh TEXT,
    applicant TEXT,
    approval_date TEXT,
    license_number TEXT,
    url TEXT,
    source TEXT,
    first_seen TEXT DEFAULT (datetime('now')),
    last_seen TEXT DEFAULT (datetime('now')),
    UNIQUE(country, license_number, product_name)
);
CREATE INDEX IF NOT EXISTS idx_api_en ON products(api_en);
CREATE INDEX IF NOT EXISTS idx_api_zh ON products(api_zh);
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def get_conn():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def load_config(name):
    with open(CONFIG_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def upsert_products(conn, records):
    """records: list of dicts with keys country/authority/product_name/api_en/api_zh/
    applicant/approval_date/license_number/url/source"""
    cur = conn.cursor()
    n_new, n_seen = 0, 0
    for r in records:
        cur.execute(
            """
            INSERT INTO products (country, authority, product_name, api_en, api_zh,
                                  applicant, approval_date, license_number, url, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(country, license_number, product_name)
            DO UPDATE SET last_seen = datetime('now'),
                          approval_date = COALESCE(excluded.approval_date, products.approval_date),
                          url = COALESCE(excluded.url, products.url)
            """,
            (
                r.get("country", ""),
                r.get("authority", ""),
                r.get("product_name", ""),
                (r.get("api_en") or "").strip().lower(),
                r.get("api_zh"),
                r.get("applicant"),
                r.get("approval_date"),
                r.get("license_number"),
                r.get("url"),
                r.get("source"),
            ),
        )
        if cur.rowcount and cur.lastrowid:
            n_new += 1
        else:
            n_seen += 1
    conn.commit()
    return n_new, n_seen


def set_meta(conn, key, value):
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()


def get_meta(conn, key, default=None):
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def query_by_api(conn, api_en, api_zh=None):
    api_en = (api_en or "").strip().lower()
    rows = conn.execute(
        """
        SELECT * FROM products
        WHERE api_en LIKE ? OR (api_zh IS NOT NULL AND api_zh LIKE ?)
        ORDER BY country, approval_date DESC
        """,
        (f"%{api_en}%", f"%{api_zh}%" if api_zh else "\x00"),
    ).fetchall()
    return rows
