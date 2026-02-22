import streamlit as st
import os
import base64
from database import init_db, migrate_staff_table

# ==================================
# 初期設定（最上部）
# ==================================
st.set_page_config(
    page_title="BAR給与管理システム",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================================
# DB初期化
# ==================================
init_db()
migrate_staff_table()

# ==================================
# セッション管理
# ==================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "page" not in st.session_state:
    st.session_state.page = "sales_csv"

# ==================================
# ロゴ設定
# ==================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo.png")

def get_base64_logo():
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


# ==================================
# ログイン画面
# ==================================
if not st.session_state.logged_in:

    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0d1b2a, #1b263b);
    }
    [data-testid="stSidebar"] {display:none;}
    </style>
    """, unsafe_allow_html=True)

    logo_base64 = get_base64_logo()
    if logo_base64:
        st.markdown(f"""
        <div style="text-align:center; margin-top:60px;">
            <img src="data:image/png;base64,{logo_base64}" width="260">
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<h2 style='text-align:center;color:white;'>給与管理システム</h2>", unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("ユーザーID")
        password = st.text_input("パスワード", type="password")
        submitted = st.form_submit_button("ログイン")

        if submitted:
            if username == "admin" and password == "Tqv:32566":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("IDまたはパスワードが違います")


# ==================================
# ログイン後（完全SaaSルーター）
# ==================================
else:

    from ui.layout import sidebar
    from modules import (
        sales_csv,
        sales_analysis,
        salary,
        transfer,
        staff_master,
        salary_rules,
        bank_master,
        salary_explanation
    )

    # サイドバー描画
    sidebar()

    page = st.session_state.page

    # ルーティング
    if page == "sales_csv":
        sales_csv.main()

    elif page == "sales_analysis":
        sales_analysis.main()

    elif page == "salary":
        salary.main()

    elif page == "transfer":
        transfer.main()

    elif page == "staff_master":
        staff_master.main()

    elif page == "salary_rules":
        salary_rules.main()

    elif page == "bank_master":
        bank_master.main()
    
    elif page == "salary_explanation":
        salary_explanation.main()
    