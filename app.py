import streamlit as st

from ui.ui_style import apply_global_style
from ui.sidebar import render_sidebar

apply_global_style()
render_sidebar()

import streamlit as st

# ===== パスワード認証 =====
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    password = st.text_input("パスワードを入力してください", type="password")

    if st.button("ログイン"):
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("パスワードが違います")

    return False


if not check_password():
    st.stop()