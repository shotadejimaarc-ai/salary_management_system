import streamlit as st


# =============================
# ダーク高級スタイル
# =============================
def apply_dark_bank_style():
    st.markdown("""
        <style>
                
        /* ===== ページ全体を左上寄せ ===== */
        .block-container {
            padding-top: 1rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 100% !important;
        }

        /* 上部余白削除 */
        header {
            visibility: hidden;
        }

        /* ===== ダーク銀行テーマ ===== */
        body {
            background-color: #0b1120;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a, #111827);
        }

        .sidebar-title {
            font-size: 20px;
            font-weight: 600;
            color: #e5e7eb;
            padding-bottom: 10px;
        }

        .category-label {
            font-size: 12px;
            letter-spacing: 1px;
            color: #9ca3af;
            margin-top: 25px;
            margin-bottom: 8px;
        }

        div.stButton > button {
            background-color: #1f2937;
            color: #e5e7eb;
            border: 1px solid #374151;
            border-radius: 8px;
            padding: 10px;
            transition: all 0.2s ease-in-out;
        }

        div.stButton > button:hover {
            background-color: #374151;
            border-color: #6b7280;
        }

        div.stButton > button:focus {
            outline: none;
            border: 1px solid #60a5fa;
            box-shadow: 0 0 0 1px #60a5fa;
        }
        </style>
    """, unsafe_allow_html=True)


# =============================
# サイドバー（カテゴリ分け）
# =============================
# def sidebar():

#     apply_dark_bank_style()

#     with st.sidebar:

#         st.markdown('<div class="sidebar-title">🏦 給与管理システム</div>', unsafe_allow_html=True)

#         # =============================
#         # 売上関連
#         # =============================
#         st.markdown('<div class="category-label">SALES MANAGEMENT</div>', unsafe_allow_html=True)

#         if st.button("📂 売上CSV取込", use_container_width=True):
#             st.session_state.page = "sales_csv"

#         if st.button("📊 売上分析", use_container_width=True):
#             st.session_state.page = "sales_analysis"

#         # =============================
#         # 給与関連
#         # =============================
#         st.markdown('<div class="category-label">SALARY MANAGEMENT</div>', unsafe_allow_html=True)

#         if st.button("💰 給与計算", use_container_width=True):
#             st.session_state.page = "salary"

#         if st.button("🏦 振込データ出力", use_container_width=True):
#             st.session_state.page = "transfer"

#         # =============================
#         # マスタ管理
#         # =============================
#         st.markdown('<div class="category-label">MASTER DATA</div>', unsafe_allow_html=True)

#         if st.button("👤 担当者マスタ管理", use_container_width=True):
#             st.session_state.page = "staff_master"

#         if st.button("💹 給与ルール管理", use_container_width=True):
#             st.session_state.page = "salary_rules"

#         if st.button("🏛 銀行マスタ管理", use_container_width=True):
#             st.session_state.page = "bank_master"
        
#         # =============================
#         # 説明管理
#         # =============================
#         st.markdown('<div class="category-label">EXPLANATION</div>', unsafe_allow_html=True)

#         if st.button("📕 報酬算出ルール", use_container_width=True):
#             st.session_state.page = "salary_explanation"
        

#         # =============================
#         # ログアウト
#         # =============================
#         st.markdown("---")

#         if st.button("🚪 ログアウト", use_container_width=True):
#             st.session_state.logged_in = False
#             st.rerun()
import streamlit as st


# =============================
# ダーク高級スタイル
# =============================
def apply_dark_bank_style():
    st.markdown("""
        <style>
        .block-container {
            padding-top: 1rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 100% !important;
        }

        header { visibility: hidden; }

        body { background-color: #0b1120; }

        .sidebar-box {
            background: linear-gradient(180deg, #0f172a, #111827);
            padding: 20px;
            border-radius: 12px;
        }

        .sidebar-title {
            font-size: 20px;
            font-weight: 600;
            color: #e5e7eb;
            padding-bottom: 10px;
        }

        .category-label {
            font-size: 12px;
            letter-spacing: 1px;
            color: #9ca3af;
            margin-top: 25px;
            margin-bottom: 8px;
        }

        div.stButton > button {
            background-color: #1f2937;
            color: #e5e7eb;
            border: 1px solid #374151;
            border-radius: 8px;
            padding: 10px;
        }

        div.stButton > button:hover {
            background-color: #374151;
        }
        </style>
    """, unsafe_allow_html=True)


# =============================
# 自作サイドバー付きレイアウト
# =============================
def render_layout():

    apply_dark_bank_style()

    if "sidebar_open" not in st.session_state:
        st.session_state.sidebar_open = True

    # レイアウト分岐
    if st.session_state.sidebar_open:
        col_sidebar, col_main = st.columns([2, 8])
    else:
        col_sidebar, col_main = st.columns([0.5, 9.5])

    # =============================
    # サイドバー
    # =============================
    with col_sidebar:

        if st.session_state.sidebar_open:
            st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)

            if st.button("<<"):
                st.session_state.sidebar_open = False
                st.rerun()

            st.markdown('<div class="sidebar-title">🏦 給与管理システム</div>', unsafe_allow_html=True)

            st.markdown('<div class="category-label">SALES MANAGEMENT</div>', unsafe_allow_html=True)

            if st.button("📂 売上CSV取込", use_container_width=True):
                st.session_state.page = "sales_csv"

            if st.button("📊 売上分析", use_container_width=True):
                st.session_state.page = "sales_analysis"

            st.markdown('<div class="category-label">SALARY MANAGEMENT</div>', unsafe_allow_html=True)

            if st.button("💰 給与計算", use_container_width=True):
                st.session_state.page = "salary"

            if st.button("🏦 振込データ出力", use_container_width=True):
                st.session_state.page = "transfer"

            st.markdown('<div class="category-label">MASTER DATA</div>', unsafe_allow_html=True)

            if st.button("👤 担当者マスタ管理", use_container_width=True):
                st.session_state.page = "staff_master"

            if st.button("💹 給与ルール管理", use_container_width=True):
                st.session_state.page = "salary_rules"

            if st.button("🏛 銀行マスタ管理", use_container_width=True):
                st.session_state.page = "bank_master"

            st.markdown('<div class="category-label">EXPLANATION</div>', unsafe_allow_html=True)

            if st.button("📕 報酬算出ルール", use_container_width=True):
                st.session_state.page = "salary_explanation"

            st.markdown("---")

            if st.button("🚪 ログアウト", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        else:
            if st.button(">>"):
                st.session_state.sidebar_open = True
                st.rerun()

    # =============================
    # メインエリアを返す
    # =============================
    return col_main
        

# =============================
# メイン画面制御
# =============================

if st.session_state.page == "salary_explanation":
    from modules.salary_explanation import render
    render()


