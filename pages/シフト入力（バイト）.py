from ui.ui_style import apply_global_style
from ui.sidebar import render_sidebar
import streamlit as st
import pandas as pd
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta

from queries import q_baito_staff, q_baito_shift_month, upsert_baito_shift_month
if not st.session_state.get("authenticated", False):
    st.switch_page("app.py")

st.set_page_config(page_title="シフト入力（バイト）", layout="wide")

st.markdown(
    """
<style>
.block-container{
  padding-top: 4.2rem !important;
  padding-left: 1.2rem;
  padding-right: 1.2rem;
  max-width: 1400px;
}
.big-title{ font-size: 2.2rem; font-weight: 900; margin: 0 0 0.2rem 0; }
.subtle{ color: rgba(255,255,255,0.68); margin-bottom: 0.8rem; }
.card{
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 14px;
  padding: 1rem 1rem;
  background: rgba(255,255,255,0.03);
}
hr{ border: none; border-top: 1px solid rgba(255,255,255,0.12); margin: 1.0rem 0; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="big-title">📅シフト入力（バイト）</div>', unsafe_allow_html=True)
st.markdown('<div class="subtle">毎月のバイト給与計算に必要な情報（時給・稼働時間・交通費・出勤日数）を入力します</div>', unsafe_allow_html=True)
st.markdown("<hr/>", unsafe_allow_html=True)

# 対象月
colA, colB= st.columns([1, 1])

with colA:
    ym = st.text_input("対象月（YYYY-MM）※例：2026-03 のように入力", value=date.today().strftime("%Y-%m"))

with colB:
    copy_prev = st.button("前月コピー")


    


# staff（baito）一覧
df_baito = q_baito_staff().copy()
df_baito["staff_id"] = df_baito["staff_id"].astype(str)

# 既入力（その月）
df_exist = q_baito_shift_month(ym).copy()
if not df_exist.empty:
    df_exist["staff_id"] = df_exist["staff_id"].astype(str)

# マージして編集用DataFrameを作る
base = df_baito[["staff_id", "name"]].copy()
df = base.merge(df_exist, on="staff_id", how="left")

if copy_prev:
    try:
        base_date = datetime.strptime(ym + "-01", "%Y-%m-%d")
        prev_month = (base_date - relativedelta(months=1)).strftime("%Y-%m")

        df_prev = q_baito_shift_month(prev_month).copy()
        if not df_prev.empty:
            df_prev["staff_id"] = df_prev["staff_id"].astype(str)

            df = base.merge(df_prev, on="staff_id", how="left")

            for c, default in [
                ("hourly_wage", 0),
                ("total_hours", 0.0),
                ("transport_one_way", 0),
                ("attendance_days", 0),
            ]:
                if c not in df.columns:
                    df[c] = default
                df[c] = df[c].fillna(default)

            st.success(f"{prev_month} のシフトをコピーしました（保存はまだされていません）")
        else:
            st.warning("前月データが存在しません")

    except Exception:
        st.error("対象月の形式が不正です")

# 初期値（未入力は0）
for c, default in [
    ("hourly_wage", 0),
    ("total_hours", 0.0),
    ("transport_one_way", 0),
    ("attendance_days", 0),
]:
    if c not in df.columns:
        df[c] = default
    df[c] = df[c].fillna(default)

st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("入力")
st.caption("※「保存」を押すまでDBには反映されません。")

# 編集テーブル（シンプル）
edited = st.data_editor(
    df.rename(columns={
        "staff_id":"ID",
        "name":"名前",
        "hourly_wage":"時給",
        "total_hours":"稼働時間(合計)",
        "transport_one_way":"交通費(片道)",
        "attendance_days":"出勤日数",
    }),
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
)

st.markdown("<hr/>", unsafe_allow_html=True)
save = st.button("保存（この月の入力を確定）", type="primary", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if save:
    # YYYY-MM -> date(YYYY,MM,1)
    try:
        y, m = ym.split("-")
        target_month_date = date(int(y), int(m), 1)
    except Exception:
        st.error("対象月の形式が不正です。YYYY-MM で入力してください。")
        st.stop()

    # 保存
    for _, r in edited.iterrows():
        staff_id = str(r["ID"])
        upsert_baito_shift_month(
            target_month_date=target_month_date,
            staff_id=staff_id,
            hourly_wage=int(r["時給"] or 0),
            total_hours=float(r["稼働時間(合計)"] or 0),
            transport_one_way=int(r["交通費(片道)"] or 0),
            attendance_days=int(r["出勤日数"] or 0),
        )

    st.success("保存しました。")
    st.rerun()