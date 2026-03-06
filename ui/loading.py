import streamlit as st

def show_loading(message="画面を読み込み中です..."):
    box = st.empty()
    bar = st.progress(0)

    box.markdown(f"""
    <div style="
        padding: 18px 20px;
        border-radius: 18px;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,215,120,0.18);
        color: rgba(255,255,255,0.88);
        font-weight: 700;
    ">
        ⏳ {message}
    </div>
    """, unsafe_allow_html=True)

    return box, bar


def clear_loading(box, bar):
    box.empty()
    bar.empty()