import streamlit as st


# =============================
# ダークスタイル
# =============================
def apply_dark_bank_style():
    st.markdown("""
    <style>

    /* ヘッダー削除 */
    header {visibility:hidden;}
    [data-testid="stHeader"] {visibility:hidden;}

    /* 上余白だけ削る */
    .block-container {
        padding-top: 0rem !important;
    }

    body {
        background-color: #0b1120;
    }

    .sidebar-box {
        background: linear-gradient(180deg, #0f172a, #111827);
        padding: 20px;
        border-radius: 14px;
    }
                
    [data-testid="column"] > div {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
    }

    </style>
    """, unsafe_allow_html=True)


# =============================
# レイアウト
# =============================
def render_layout():

    apply_dark_bank_style()

    if "sidebar_open" not in st.session_state:
        st.session_state.sidebar_open = True

    # 列幅調整
    if st.session_state.sidebar_open:
        col_sidebar, col_main = st.columns([2, 8])
    else:
        col_sidebar, col_main = st.columns([0.6, 9.4])

    # =============================
    # サイドバー
    # =============================
    with col_sidebar:

        st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)

        # トグルボタン
        if st.button("<<" if st.session_state.sidebar_open else ">>"):
            st.session_state.sidebar_open = not st.session_state.sidebar_open
            st.rerun()

        if st.session_state.sidebar_open:

            st.markdown('<div class="sidebar-title">🏦 給与管理</div>', unsafe_allow_html=True)

            st.markdown('<div class="category-label">SALES</div>', unsafe_allow_html=True)
            if st.button("📂 売上CSV取込", width="stretch"):
                st.session_state.page = "sales_csv"
            if st.button("📊 売上分析", width="stretch"):
                st.session_state.page = "sales_analysis"

            st.markdown('<div class="category-label">SALARY</div>', unsafe_allow_html=True)
            if st.button("💰 給与計算", width="stretch"):
                st.session_state.page = "salary"
            if st.button("🏦 振込データ出力", width="stretch"):
                st.session_state.page = "transfer"

            st.markdown('<div class="category-label">MASTER</div>', unsafe_allow_html=True)
            if st.button("👤 担当者管理", width="stretch"):
                st.session_state.page = "staff_master"
            if st.button("💹 ルール管理", width="stretch"):
                st.session_state.page = "salary_rules"
            if st.button("🏛 銀行管理", width="stretch"):
                st.session_state.page = "bank_master"

            st.markdown('<div class="category-label">EXPLANATION</div>', unsafe_allow_html=True)
            if st.button("📕 報酬算出ルール", width="stretch"):
                st.session_state.page = "salary_explanation"
            

            st.markdown("---")
            if st.button("🚪 ログアウト", width="stretch"):
                st.session_state.logged_in = False
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    return col_main