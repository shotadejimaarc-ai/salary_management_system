import streamlit as st
import pandas as pd
from datetime import date

from ui.ui_style import apply_global_style
apply_global_style()
from ui.sidebar import render_sidebar
render_sidebar()

from queries import (
    q_staff_master_all,
    q_sales_total_month,
    q_staff_sales_detail_month,
)

st.set_page_config(page_title="売上分析", layout="wide")
apply_global_style()
render_sidebar()
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
st.markdown('<div class="big-title">🧾売上分析</div>', unsafe_allow_html=True)
st.markdown('<div class="subtle">対象月の合計売上と、担当者別の売上明細を確認します</div>', unsafe_allow_html=True)
st.markdown("<hr/>", unsafe_allow_html=True)

def to_year_month(d: date) -> str:
    return d.strftime("%Y-%m")

# =============================
# 対象月
# =============================
c1, c2 = st.columns([1.2, 2.8], gap="large")

with c1:
    base = date.today().replace(day=1)
    d = st.date_input("対象月（YYYY-MM）", value=base)
    year_month = to_year_month(d)

with c2:
    # 月合計売上（KPI）
    try:
        df_total = q_sales_total_month(year_month)
        total = int(df_total["sales_total"].iloc[0]) if not df_total.empty else 0
    except Exception as e:
        total = 0
        st.error(f"月合計売上の取得に失敗: {e}")

    st.markdown(
        f"""
        <div class="card" style="padding:1.1rem 1.2rem;">
          <div class="hint">対象月の合計売上</div>
          <div style="font-size:2.1rem; font-weight:900; margin-top:0.25rem;">
            ¥ {total:,.0f}
          </div>
          <div class="hint" style="margin-top:0.35rem;">
            ※ payments 合計（支払いベース）で集計
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<hr/>", unsafe_allow_html=True)

# =============================
# 担当者選択
# =============================
df_staff = q_staff_master_all().copy()
df_staff["staff_id"] = df_staff["staff_id"].astype(str)

# 表示ラベル（ID順）
df_staff = df_staff.sort_values("staff_id")
staff_opts = [""] + df_staff.apply(lambda r: f"{r['staff_id']}｜{r['name']}", axis=1).tolist()

left, right = st.columns([1.25, 2.75], gap="large")

with left:
    st.markdown('<div class="section-title">担当者を選択<span class="badge">検索</span></div>', unsafe_allow_html=True)
    kw = st.text_input("検索（名前 / staff_id）", "")

    df_pick = df_staff.copy()
    if kw.strip():
        k = kw.strip().lower()
        df_pick = df_pick[
            df_pick["staff_id"].str.lower().str.contains(k)
            | df_pick["name"].astype(str).str.lower().str.contains(k)
        ]

    df_pick = df_pick.sort_values("staff_id")
    staff_opts2 = [""] + df_pick.apply(lambda r: f"{r['staff_id']}｜{r['name']}", axis=1).tolist()
    staff_label = st.selectbox("担当者", staff_opts2, index=0)

    st.caption("一覧（参照用）")
    st.dataframe(
        df_pick[["staff_id", "name", "type"]].rename(columns={"staff_id":"ID","name":"名前","type":"種別"}),
        use_container_width=True,
        hide_index=True
    )

with right:
    st.markdown('<div class="section-title">売上明細</div>', unsafe_allow_html=True)
    st.markdown('<div class="hint">担当者を選ぶと、対象月に紐づく売上明細を一覧表示します。</div>', unsafe_allow_html=True)
    st.markdown("<hr/>", unsafe_allow_html=True)

    if not staff_label:
        st.info("左で担当者を選択してください。")
        st.stop()

    staff_id = staff_label.split("｜")[0].strip()

    # 追加おすすめ：明細の簡易フィルタ
    f1, f2, f3 = st.columns([1.3, 1.3, 1.4])
    with f1:
        keyword_item = st.text_input("明細検索（商品名/カテゴリ）", "")
    with f2:
        limit = st.selectbox("表示件数", [200, 500, 1000, 2000], index=1)
    with f3:
        st.caption("※重い場合は件数を下げてね")

    try:
        df_detail = q_staff_sales_detail_month(year_month, staff_id).copy()
    except Exception as e:
        st.error(f"売上明細の取得に失敗: {e}")
        st.stop()

    if df_detail.empty:
        st.info("この担当者の売上明細がありません。")
        st.stop()

    # フィルタ
    if keyword_item.strip():
        k = keyword_item.strip().lower()
        cols = [c for c in ["item_name", "category_name"] if c in df_detail.columns]
        if cols:
            mask = False
            for c in cols:
                mask = mask | df_detail[c].astype(str).str.lower().str.contains(k)
            df_detail = df_detail[mask]

    # 並び + limit
    if "created_at" in df_detail.columns:
        df_detail = df_detail.sort_values("created_at", ascending=False)

    df_detail = df_detail.head(int(limit))


    # KPI（担当者の月売上合計）
    if "line_total" in df_detail.columns:
        staff_total = int(pd.to_numeric(df_detail["line_total"], errors="coerce").fillna(0).sum())
        st.metric("担当者売上", f"¥ {staff_total:,.0f}")


    # 日本語ヘッダー
    col_map = {
        "created_at": "日時",
        "order_id": "注文ID",
        "menu_name": "メニュー",
        "qty": "数量",
        "unit_price": "単価",
        "line_total": "小計",
        "is_paid": "支払済",
    }

    df_show = df_detail.rename(columns=col_map)


    # 表示順
    preferred = [
        "日時",
        "注文ID",
        "メニュー",
        "数量",
        "単価",
        "小計",
        "支払済",
    ]

    show_cols = [c for c in preferred if c in df_show.columns]


    st.dataframe(
        df_show[show_cols],
        use_container_width=True,
        hide_index=True
    )

    # 追加おすすめ：CSV出力（現場で便利）
    csv = df_detail.to_csv(index=False).encode("utf-8-sig")
    st.download_button("この明細をCSVダウンロード", csv, file_name=f"sales_detail_{year_month}_{staff_id}.csv", use_container_width=True)