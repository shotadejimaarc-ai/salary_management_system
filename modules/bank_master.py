

import streamlit as st
import pandas as pd
import sqlite3
import requests
import time
from datetime import datetime

DB_PATH = "app.db"


# =============================
# DB接続
# =============================
def get_connection():
    return sqlite3.connect(DB_PATH)


# =============================
# テーブル初期化
# =============================
def init_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS banks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_code TEXT UNIQUE,
            bank_name TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_code TEXT,
            branch_code TEXT,
            branch_name TEXT,
            created_at TEXT,
            updated_at TEXT,
            UNIQUE(bank_code, branch_code)
        )
    """)

    conn.commit()
    conn.close()


# =============================
# API取得処理
# =============================
def fetch_all_banks():
    banks = []
    page = 1

    while True:
        url = f"https://bank.teraren.com/banks.json?page={page}"
        res = requests.get(url)

        if res.status_code != 200:
            break

        data = res.json()
        if not data:
            break

        banks.extend(data)
        page += 1
        time.sleep(0.2)

    return banks


def fetch_branches_for_bank(bank_code):
    branches = []
    page = 1

    while True:
        url = f"https://bank.teraren.com/banks/{bank_code}/branches.json?page={page}"
        res = requests.get(url)

        if res.status_code != 200:
            break

        data = res.json()
        if not data:
            break

        branches.extend(data)
        page += 1
        time.sleep(0.2)

    return branches


# =============================
# API → 洗い替え登録
# =============================
def refresh_from_api():
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        cur.execute("BEGIN")

        cur.execute("DELETE FROM branches")
        cur.execute("DELETE FROM banks")

        banks = fetch_all_banks()

        progress = st.progress(0)
        total = len(banks)

        for i, bank in enumerate(banks):
            bank_code = str(bank.get("code")).zfill(4)
            bank_name = bank.get("name")

            cur.execute("""
                INSERT INTO banks (bank_code, bank_name, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (bank_code, bank_name, now, now))

            branches = fetch_branches_for_bank(bank_code)

            for b in branches:
                branch_code = str(b.get("code")).zfill(3)
                branch_name = b.get("name")

                cur.execute("""
                    INSERT INTO branches
                    (bank_code, branch_code, branch_name, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    bank_code,
                    branch_code,
                    branch_name,
                    now,
                    now
                ))

            progress.progress((i + 1) / total)

        conn.commit()
        st.success("APIから銀行マスタを更新しました。")

    except Exception as e:
        conn.rollback()
        st.error(f"更新失敗: {e}")

    finally:
        conn.close()


# =============================
# CSV洗い替え登録
# =============================
def refresh_from_csv(df):
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        cur.execute("BEGIN")

        cur.execute("DELETE FROM branches")
        cur.execute("DELETE FROM banks")

        df["bank_code"] = df["bank_code"].astype(str).str.zfill(4)
        df["branch_code"] = df["branch_code"].astype(str).str.zfill(3)

        banks_df = df[["bank_code", "bank_name"]].drop_duplicates()

        for _, row in banks_df.iterrows():
            cur.execute("""
                INSERT INTO banks (bank_code, bank_name, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (row["bank_code"], row["bank_name"], now, now))

        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO branches
                (bank_code, branch_code, branch_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                row["bank_code"],
                row["branch_code"],
                row["branch_name"],
                now,
                now
            ))

        conn.commit()
        st.success("CSVから銀行マスタを更新しました。")

    except Exception as e:
        conn.rollback()
        st.error(f"取込失敗: {e}")

    finally:
        conn.close()


# =============================
# 検索
# =============================
def search_bank_data(keyword):
    conn = get_connection()

    query = """
        SELECT b.bank_code, b.bank_name,
            br.branch_code, br.branch_name
        FROM banks b
        JOIN branches br
        ON b.bank_code = br.bank_code
        WHERE b.bank_code LIKE ?
        OR b.bank_name LIKE ?
        OR br.branch_code LIKE ?
        OR br.branch_name LIKE ?
        ORDER BY b.bank_code, br.branch_code
    """

    df = pd.read_sql_query(query, conn, params=[f"%{keyword}%"] * 4)
    conn.close()
    return df


# =============================
# メイン画面
# =============================
def main():
    
    from ui.ui_style import apply_global_style
    apply_global_style()

    st.markdown("""
    <div class="sticky-header">
        <h2>🏦 銀行マスタ管理</h2>
    </div>
    """, unsafe_allow_html=True)
    tab1, tab2 ,tab3= st.tabs(["銀行データ取得", "銀行データ取り込み", "銀行情報一覧"])
    init_tables()


    # =============================
    # タブ1：API取得
    # =============================
    with tab1:

        st.markdown("### APIから銀行データ取得")
        st.warning("⚠ 既存データは全削除されます（洗い替え）")

        if st.button("最新の銀行データを取得して更新"):
            refresh_from_api()

    # =============================
    # タブ2：CSV取込
    # =============================
    with tab2:

        st.markdown("### CSV取込（フォーマット固定）")

        uploaded_file = st.file_uploader("CSVアップロード", type="csv")

        if uploaded_file:
            df = pd.read_csv(uploaded_file, dtype=str)

            required_columns = [
                "bank_code",
                "bank_name",
                "branch_code",
                "branch_name"
            ]

            df["bank_code"] = df["bank_code"].astype(str).str.zfill(4)
            df["branch_code"] = df["branch_code"].astype(str).str.zfill(3)

            if not all(col in df.columns for col in required_columns):
                st.error("CSVフォーマットが正しくありません。")
                st.stop()

            st.dataframe(df.head(10))

            if st.button("CSVで銀行マスタを洗い替え更新"):
                refresh_from_csv(df)

    # =============================
    # タブ3：一覧
    # =============================
    with tab3:

        st.markdown("### 銀行情報一覧")

        keyword = st.text_input("検索")

        if keyword:
            df = search_bank_data(keyword)
        else:
            df = search_bank_data("")

        st.dataframe(df, use_container_width=True)

