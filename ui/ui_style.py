import streamlit as st

def apply_global_style():
    st.markdown("""
    <style>
    /* =========================
       ① 高級バーっぽい「照明」背景
       ========================= */
    .stApp, .main{
      background:
        radial-gradient(900px 420px at 50% 20%, rgba(255,215,120,0.10), transparent 60%),
        radial-gradient(700px 320px at 50% 60%, rgba(60,255,122,0.05), transparent 55%),
        linear-gradient(180deg, #0A0F18 0%, #070A10 65%, #05070C 100%) !important;
    }
    /* ===== Streamlit Cloudの上部メニューを非表示 ===== */
    header[data-testid="stHeader"]{
        display: none;
    }

    /* コンテンツ幅/余白（任意：見た目安定） */
    .block-container{
      padding-top: 4.2rem !important;
      max-width: 1400px;
    }

    /* =========================
       ② サイドバー：高級カード化（ガラス＋深いグラデ）
       ========================= */

    section[data-testid="stSidebar"]{
      background: linear-gradient(180deg, #0f1724 0%, #0b0f18 100%) !important;
      backdrop-filter: blur(12px);
      border-right: 1px solid rgba(255,255,255,0.08);
    }

    /* サイドバー外枠の最上部余白をかなり詰める */
    section[data-testid="stSidebar"] > div:first-child{
      padding-top: 0px !important;
    }
    section[data-testid="stSidebar"] .block-container{
      padding-top: 0rem !important;
    }

    /* サイドバー内部余白 */
    section[data-testid="stSidebar"] .block-container{
      padding-top: 0.35rem !important;
      padding-left: 0.9rem !important;
      padding-right: 0.9rem !important;
      padding-bottom: 1rem !important;
    }

    /* Streamlit標準ページ一覧を消す */
    section[data-testid="stSidebar"] nav,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"],
    section[data-testid="stSidebar"] [aria-label="Sidebar navigation"],
    section[data-testid="stSidebar"] ul[role="list"],
    section[data-testid="stSidebar"] div[data-testid="stSidebarNavItems"]{
      display: none !important;
    }

    /* サイドバー内のタイトル・見出し系の余白を詰める */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p{
      margin-top: 0 !important;
    }

    /* サイドバーの見出し（###） */
    section[data-testid="stSidebar"] h3{
      margin: 0.65rem 0 0.20rem 0 !important;
      font-size: 0.95rem;
      opacity: 0.78;
      letter-spacing: 0.04em;
    }

    /* 区切り線 */
    section[data-testid="stSidebar"] hr{
      border: none;
      border-top: 1px solid rgba(255,255,255,0.10);
      margin: 0.65rem 0 0.75rem 0 !important;
    }

    /* 自作メニュー（page_link）の見た目を「高級ボタン化」 */
    section[data-testid="stSidebar"] a{
      display:block;
      padding: 10px 12px;
      border-radius: 12px;
      margin: 6px 0;
      text-decoration: none !important;

      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.06);
      color: rgba(255,255,255,0.86) !important;

      transition: all .22s ease;
    }

    section[data-testid="stSidebar"] a:hover{
      transform: translateY(-1px);
      background: rgba(60,255,122,0.10);
      border: 1px solid rgba(60,255,122,0.22);
      color: rgba(60,255,122,0.95) !important;
      box-shadow: 0 0 18px rgba(60,255,122,0.12);
    }

    /* =========================
       ③ ボタンをネオン化（全ページ）
       ========================= */
    div.stButton > button{
      border-radius: 12px !important;
      border: 1px solid rgba(60,255,122,0.35) !important;
      background: rgba(60,255,122,0.08) !important;
      color: rgba(255,255,255,0.92) !important;
      font-weight: 800 !important;
      transition: all .25s ease !important;
    }

    div.stButton > button:hover{
      background: rgba(60,255,122,0.18) !important;
      box-shadow: 0 0 18px rgba(60,255,122,0.30) !important;
      transform: translateY(-1px) !important;
    }

    /* ボタンのフォーカス枠が派手なら抑える */
    div.stButton > button:focus{
      outline: none !important;
      box-shadow: 0 0 0 2px rgba(60,255,122,0.15) !important;
    }

    </style>
    """, unsafe_allow_html=True)