"""SQLite: lưu tài liệu, nhãn gốc (gold) và kết quả trích rút của từng phương pháp."""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "invoices.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id         TEXT PRIMARY KEY,      -- vd: sroie/X51005200931
    dataset    TEXT NOT NULL,         -- sroie | mcocr
    lang       TEXT NOT NULL,         -- en | vi
    split      TEXT NOT NULL,         -- train | dev | test
    image_path TEXT,
    raw_text   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS gold (
    doc_id  TEXT PRIMARY KEY REFERENCES documents(id),
    seller  TEXT, address TEXT, date TEXT, total TEXT
);
CREATE TABLE IF NOT EXISTS extractions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id        TEXT NOT NULL REFERENCES documents(id),
    method        TEXT NOT NULL,      -- regex | gemini-zs | gemini-fs | qwen2.5-3b | qwen2.5-7b
    model_version TEXT,               -- phiên bản model thực tế mà API trả về
    seller TEXT, address TEXT, date TEXT, total TEXT,
    raw_output    TEXT,
    valid_json    INTEGER,
    latency_ms    INTEGER,
    tokens_in     INTEGER,
    tokens_out    INTEGER,
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (doc_id, method)
);
"""


def connect(path=DB_PATH):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def insert_document(con, doc):
    con.execute(
        "INSERT OR REPLACE INTO documents (id, dataset, lang, split, image_path, raw_text) VALUES (?,?,?,?,?,?)",
        (doc["id"], doc["dataset"], doc["lang"], doc["split"], doc.get("image_path"), doc["text"]),
    )
    g = doc["gold"]
    con.execute(
        "INSERT OR REPLACE INTO gold (doc_id, seller, address, date, total) VALUES (?,?,?,?,?)",
        (doc["id"], g.get("seller"), g.get("address"), g.get("date"), g.get("total")),
    )


def has_extraction(con, doc_id, method):
    return con.execute(
        "SELECT 1 FROM extractions WHERE doc_id=? AND method=?", (doc_id, method)
    ).fetchone() is not None


def save_extraction(con, doc_id, method, fields, raw_output=None, valid_json=True,
                    latency_ms=None, tokens_in=None, tokens_out=None, model_version=None):
    con.execute(
        """INSERT OR REPLACE INTO extractions
           (doc_id, method, model_version, seller, address, date, total,
            raw_output, valid_json, latency_ms, tokens_in, tokens_out)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (doc_id, method, model_version,
         fields.get("seller"), fields.get("address"), fields.get("date"), fields.get("total"),
         raw_output if isinstance(raw_output, (str, type(None))) else json.dumps(raw_output, ensure_ascii=False),
         int(bool(valid_json)), latency_ms, tokens_in, tokens_out),
    )
    con.commit()
