# db.py
import os
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor

def _get_database_url() -> str:
    # 1) Streamlit secrets 優先
    try:
        url = st.secrets["DATABASE_URL"]
        if url:
            return url
    except Exception:
        pass

    # 2) 環境変数フォールバック（必要なら）
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    # 3) 旧env（互換維持）
    host = os.getenv("SUPABASE_HOST")
    db = os.getenv("SUPABASE_DB", "postgres")
    user = os.getenv("SUPABASE_USER")
    password = os.getenv("SUPABASE_PASSWORD")
    port = os.getenv("SUPABASE_PORT", "5432")

    if host and user and password:
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"

    raise RuntimeError(
        "DB接続情報がありません。secrets.toml の DATABASE_URL を設定してください。"
    )

def get_conn():
    db_url = _get_database_url()

    # psycopg2 は postgresql+psycopg2 を嫌うので postgresql:// に寄せる
    db_url = db_url.replace("postgresql+psycopg2://", "postgresql://")

    return psycopg2.connect(db_url, sslmode="require")

def fetch_all(sql: str, params=None):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or {})
            return cur.fetchall()

def fetch_one(sql: str, params=None):
    rows = fetch_all(sql, params)
    return rows[0] if rows else None

def execute(sql: str, params=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or {})
        conn.commit()