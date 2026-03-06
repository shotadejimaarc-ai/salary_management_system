import streamlit as st

def render_sidebar():
    st.sidebar.markdown("""
    <div style="
        padding:16px 10px 18px 10px;
        border-bottom:1px solid rgba(255,255,255,0.10);
        margin-bottom:12px;
    ">
      <div style="
        font-size:22px;
        font-weight:900;
        letter-spacing:0.06em;
        line-height:1.2;
      ">
        給与管理システム
      </div>

      <div style="
        font-size:12px;
        opacity:0.62;
        margin-top:5px;
        letter-spacing:0.22em;
        text-transform:uppercase;
      ">
        Salary Management System
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.caption("SIDEBAR_RENDERED")

    st.sidebar.page_link("pages/Home.py", label="HOME")

    st.sidebar.markdown("---")

    st.sidebar.markdown("### 売上管理")
    st.sidebar.page_link("pages/売上分析.py", label="売上管理・分析")

    st.sidebar.markdown("---")

    st.sidebar.markdown("### 給与管理")
    st.sidebar.page_link("pages/シフト入力（バイト）.py", label="シフト入力（バイト）")
    st.sidebar.page_link("pages/給与計算・確定.py", label="給与計算・確定")
    st.sidebar.page_link("pages/銀行振込CSV出力.py", label="銀行振込CSV出力")

    st.sidebar.markdown("---")

    st.sidebar.markdown("### マスタ管理")
    st.sidebar.page_link("pages/給与ルール設定.py", label="給与ルール設定")
    st.sidebar.page_link("pages/担当者メンテナンス.py", label="担当者メンテナンス")
    st.sidebar.page_link("pages/銀行マスタ管理.py", label="銀行マスタ管理")