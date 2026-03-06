from ui.ui_style import apply_global_style
apply_global_style()

from ui.sidebar import render_sidebar
render_sidebar()
import streamlit as st
from queries import q_bank_branch_list, refresh_bank_master_from_api
if not st.session_state.get("authenticated", False):
    st.switch_page("app.py")
st.set_page_config(page_title="銀行マスタ管理", layout="wide")

st.markdown(
    """
<style>
.block-container{
  padding-top: 4.2rem !important;
  padding-left: 1.2rem;
  padding-right: 1.2rem;
  max-width: 1400px;
}
.big-title{
  font-size: 2.2rem;
  font-weight: 900;
  margin: 0 0 0.3rem 0;
}
.subtle{ color: rgba(255,255,255,0.68); margin-bottom: 0.8rem; }
hr{ border: none; border-top: 1px solid rgba(255,255,255,0.12); margin: 1.0rem 0; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="big-title">🏦 銀行マスタ管理</div>', unsafe_allow_html=True)
st.markdown('<div class="subtle">APIから銀行・支店データを取得し、DBを洗い替え更新します</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["銀行データ取得", "銀行情報一覧"])

with tab1:
    st.markdown("### APIから銀行データ取得")
    st.warning("⚠ 既存データは全削除されます（洗い替え）")

    if st.button("最新の銀行データを取得して更新", type="primary"):
        prog = st.progress(0.0)
        msg = st.empty()

        def cb(i, total, text):
            prog.progress(i / max(total, 1))
            msg.caption(f"取得中… {i}/{total} : {text}")

        try:
            result = refresh_bank_master_from_api(progress_cb=cb)
            st.success(f"更新しました：銀行 {result['banks']:,} 件 / 支店 {result['branches']:,} 件")
        except Exception as e:
            st.error(f"更新失敗: {e}")

with tab2:
    st.markdown("### 銀行情報一覧")
    keyword = st.text_input("検索（銀行コード/銀行名/支店コード/支店名）", "")

    df = q_bank_branch_list(keyword)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption("※表示は最大2000件です（検索で絞ってください）")