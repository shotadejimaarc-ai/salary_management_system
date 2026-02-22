import streamlit as st

def apply_global_style():

    st.markdown("""
    <style>

    /* =========================
       全体背景（銀行ダーク）
    ==========================*/
    .stApp {
        background: linear-gradient(135deg, #0d1b2a, #1b263b);
        color: #e5e7eb;
    }

    /* =========================
       左上寄せ + 横幅制限解除
    ==========================*/
    .block-container {
        padding-top: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }

    /* Streamlit上部の空白削除 */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* =========================
       フォント
    ==========================*/
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=Noto+Sans+JP:wght@300;400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans JP', sans-serif;
    }

    /* =========================
       サイドバー（銀行風）
    ==========================*/
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a, #111827);
        border-right: 1px solid rgba(255,255,255,0.05);
    }

    /* =========================
       Sticky Header（タイトル固定）
    ==========================*/
    .sticky-header {
        position: sticky;
        top: 0;
        z-index: 999;
        background: linear-gradient(135deg, #0d1b2a, #1b263b);
        padding-top: 10px;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }

    .sticky-header h1,
    .sticky-header h2,
    .sticky-header h3 {
        margin: 0;
        padding: 0;
        color: #ffffff;
    }

    /* =========================
       タブ固定対応
    ==========================*/
    div[data-baseweb="tab-list"] {
        position: sticky;
        top: 60px;
        z-index: 998;
        background: linear-gradient(135deg, #0d1b2a, #1b263b);
        padding-top: 5px;
        padding-bottom: 5px;
    }
    
    /* ===============================
    ULTRA TOTAL CARD
    =============================== */

    .total-wrapper {
    background: linear-gradient(145deg, #1a1d23, #14171c);
    border: 1px solid #2a2f38;
    border-radius: 16px;          /* 角丸を小さく */
    padding: 22px 28px;           /* ← ここを圧縮 */
    margin-bottom: 16px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.35);  /* 影も軽く */

    display: inline-flex;         /* ← フル幅やめる */
    flex-direction: column;
    align-items: flex-start;
    width: auto;                  /* 横幅を内容サイズに */
    min-width: 420px;             /* 崩れ防止 */
    }

    .total-main-label {
        font-size: 26px;
        font-weight: 700;
        margin-bottom: 6px;           /* 余白削減 */
        color: #e6edf3;
    }

    .total-value {
        font-size: 60px;              /* 変更なし */
        font-weight: 800;
        letter-spacing: -1px;
        margin-bottom: 8px;           /* 余白削減 */
        color: #ffffff;
    }

    .total-meta {
        font-size: 14px;
        color: #9ca3af;
        border-top: 1px solid #2a2f38;
        padding-top: 8px;             /* 締める */
        width: 100%;
    }

    </style>
    """, unsafe_allow_html=True)


