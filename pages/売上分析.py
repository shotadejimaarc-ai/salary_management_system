import streamlit as st
import pandas as pd
from datetime import date

from ui.ui_style import apply_global_style
from ui.sidebar import render_sidebar

from queries import (
    q_staff_master_all,
    q_sales_total_month,
    q_staff_sales_detail_month,
    q_baito_mapping_detail_month,
    q_baito_mapping_summary_month,
    exec_baito_mapping_update_month,
)

if not st.session_state.get("authenticated", False):
    st.switch_page("app.py")

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
.section-title{
  font-size: 1.45rem;
  font-weight: 900;
  margin: 0.4rem 0 0.6rem 0;
}
.badge{
  display:inline-block;
  padding: 0.12rem 0.6rem;
  border-radius: 999px;
  background: rgba(60,255,122,0.14);
  color: rgba(60,255,122,0.95);
  font-weight: 800;
  font-size: 0.85rem;
  margin-left: 0.4rem;
  vertical-align: middle;
}
.hint{
  color: rgba(255,255,255,0.62);
  font-size: 0.92rem;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="big-title">🧾売上分析</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtle">対象月の合計売上、担当者別売上明細、バイト明細の親スタッフマッピング候補を確認します</div>',
    unsafe_allow_html=True,
)
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
            ※ payments.business_date ベースで集計
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<hr/>", unsafe_allow_html=True)
if "baito_map_confirm_open" not in st.session_state:
    st.session_state["baito_map_confirm_open"] = False

tab1, tab2 = st.tabs(["売上分析", "バイト明細マッピング"])

# =========================================================
# Tab1: 売上分析（既存）
# =========================================================
with tab1:
    # =============================
    # 担当者選択
    # =============================
    df_staff = q_staff_master_all().copy()
    df_staff["staff_id"] = df_staff["staff_id"].astype(str)

    df_staff = df_staff.sort_values("staff_id")

    left, right = st.columns([1.25, 2.75], gap="large")

    with left:
        st.markdown('<div class="section-title">担当者を選択<span class="badge">検索</span></div>', unsafe_allow_html=True)
        kw = st.text_input("検索（名前 / staff_id）", "", key="sales_kw")

        df_pick = df_staff.copy()
        if kw.strip():
            k = kw.strip().lower()
            df_pick = df_pick[
                df_pick["staff_id"].str.lower().str.contains(k)
                | df_pick["name"].astype(str).str.lower().str.contains(k)
            ]

        df_pick = df_pick.sort_values("staff_id")
        staff_opts2 = [""] + df_pick.apply(lambda r: f"{r['staff_id']}｜{r['name']}", axis=1).tolist()
        staff_label = st.selectbox("担当者", staff_opts2, index=0, key="sales_staff")

        st.caption("一覧（参照用）")
        st.dataframe(
            df_pick[["staff_id", "name", "type"]].rename(columns={"staff_id": "ID", "name": "名前", "type": "種別"}),
            use_container_width=True,
            hide_index=True,
        )

    with right:
        st.markdown('<div class="section-title">売上明細</div>', unsafe_allow_html=True)
        st.markdown('<div class="hint">担当者を選ぶと、対象月に紐づく売上明細を一覧表示します。</div>', unsafe_allow_html=True)
        st.markdown("<hr/>", unsafe_allow_html=True)

        if not staff_label:
            st.info("左で担当者を選択してください。")
        else:
            staff_id = staff_label.split("｜")[0].strip()

            f1, f2, f3 = st.columns([1.3, 1.3, 1.4])
            with f1:
                keyword_item = st.text_input("明細検索（商品名/カテゴリ）", "", key="sales_detail_kw")
            with f2:
                limit = st.selectbox("表示件数", [200, 500, 1000, 2000], index=1, key="sales_limit")
            with f3:
                st.caption("※重い場合は件数を下げてね")

            try:
                df_detail = q_staff_sales_detail_month(year_month, staff_id).copy()
            except Exception as e:
                st.error(f"売上明細の取得に失敗: {e}")
                st.stop()

            if df_detail.empty:
                st.info("この担当者の売上明細がありません。")
            else:
                if keyword_item.strip():
                    k = keyword_item.strip().lower()
                    cols = [c for c in ["menu_name", "category_name"] if c in df_detail.columns]
                    if cols:
                        mask = False
                        for c in cols:
                            mask = mask | df_detail[c].astype(str).str.lower().str.contains(k)
                        df_detail = df_detail[mask]

                if "created_at" in df_detail.columns:
                    df_detail = df_detail.sort_values("created_at", ascending=False)

                df_detail = df_detail.head(int(limit))

                if "line_total" in df_detail.columns:
                    staff_total = int(pd.to_numeric(df_detail["line_total"], errors="coerce").fillna(0).sum())
                    st.metric("担当者売上", f"¥ {staff_total:,.0f}")

                col_map = {
                    "business_date": "営業日",
                    "created_at": "日時",
                    "order_id": "注文ID",
                    "menu_name": "メニュー",
                    "category_name": "カテゴリ",
                    "qty": "数量",
                    "unit_price": "単価",
                    "line_total": "小計",
                    "is_paid": "支払済",
                }

                df_show = df_detail.rename(columns=col_map)

                preferred = [
                    "営業日",
                    "日時",
                    "注文ID",
                    "メニュー",
                    "カテゴリ",
                    "数量",
                    "単価",
                    "小計",
                    "支払済",
                ]
                show_cols = [c for c in preferred if c in df_show.columns]

                st.dataframe(
                    df_show[show_cols],
                    use_container_width=True,
                    hide_index=True,
                )

                csv = df_detail.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "この明細をCSVダウンロード",
                    csv,
                    file_name=f"sales_detail_{year_month}_{staff_id}.csv",
                    use_container_width=True,
                    key="sales_detail_csv",
                )

# =========================================================
# Tab2: バイト明細マッピング
# =========================================================
with tab2:
    st.markdown('<div class="section-title">バイト明細マッピング</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hint">バイト帰属の明細のうち、ドリンクバック以外は親スタッフへ付け替える対象を一覧表示し、一括更新できます。</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<hr/>", unsafe_allow_html=True)

    try:
        df_map = q_baito_mapping_detail_month(year_month).copy()
    except Exception as e:
        st.error(f"バイト明細マッピングの取得に失敗: {e}")
        st.stop()

    if df_map.empty:
        st.info("対象月に、バイトへ帰属している売上明細がありません。")
        st.stop()

    # 更新対象判定
    df_map["is_mapping_target"] = df_map["mapping_status"].eq("親へマッピング")

    # KPI
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("対象明細数", f"{int(df_map['is_mapping_target'].sum())}")
    with k2:
        target_amt = int(pd.to_numeric(df_map.loc[df_map["is_mapping_target"], "line_total"], errors="coerce").fillna(0).sum())
        st.metric("対象売上合計", f"¥ {target_amt:,.0f}")
    with k3:
        no_parent_cnt = int((df_map["mapping_status"] == "親未設定").sum())
        st.metric("親未設定", f"{no_parent_cnt}")
    with k4:
        multi_parent_cnt = int((df_map["mapping_status"] == "親2あり（要確認）").sum())
        st.metric("親2あり", f"{multi_parent_cnt}")

    st.markdown("---")

    # 実行前注意
    st.warning(
        "実行すると、対象月の『バイト帰属かつ非ドリンクバック』明細について、"
        "order_items.credit_staff_id を親staff_idへ更新します。"
        "親未設定・親2ありは更新対象外です。"
    )

    # 親別集計
    st.markdown("### 親スタッフ別 集計")
    try:
        df_summary = q_baito_mapping_summary_month(year_month).copy()
    except Exception as e:
        st.error(f"親スタッフ別集計の取得に失敗: {e}")
        st.stop()

    if df_summary.empty:
        st.info("更新対象となる明細はありません。")
    else:
        show_summary = df_summary.rename(columns={
            "mapped_staff_id": "親staff_id",
            "mapped_staff_name": "親スタッフ名",
            "item_count": "対象件数",
            "total_amount": "対象売上",
        })
        st.dataframe(show_summary, use_container_width=True, hide_index=True)

    # 実行エリア
    # 実行前サマリー
    target_df = df_map[df_map["mapping_status"] == "親へマッピング"].copy()
    target_count = int(len(target_df))
    target_amount = int(pd.to_numeric(target_df["line_total"], errors="coerce").fillna(0).sum()) if not target_df.empty else 0

    st.markdown("### 一括マッピング実行")

    open_col1, open_col2 = st.columns([1.4, 2.6])

    with open_col1:
        if st.button(
            "更新内容を確認する",
            disabled=(target_count == 0),
            use_container_width=True,
            key="baito_map_open_confirm",
        ):
            st.session_state["baito_map_confirm_open"] = True

    with open_col2:
        if target_count == 0:
            st.info("この月に更新対象はありません。")
        else:
            st.caption(f"対象月: {year_month} / 更新候補: {target_count}件 / 対象売上: ¥{target_amount:,}")

    # 確認ダイアログ風UI
    if st.session_state.get("baito_map_confirm_open", False) and target_count > 0:
        st.markdown(
            f"""
            <div style="
                margin-top: 0.6rem;
                margin-bottom: 1rem;
                padding: 1rem 1rem 1rem 1rem;
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.14);
                background: rgba(255, 183, 77, 0.08);
            ">
            <div style="font-size:1.05rem; font-weight:900; margin-bottom:0.45rem;">
                ⚠ 一括マッピング実行の確認
            </div>
            <div style="line-height:1.7;">
                対象月 <b>{year_month}</b> のうち、<br>
                <b>バイト帰属 × 非ドリンクバック × 親1のみ設定</b> の明細について、<br>
                <code>order_items.credit_staff_id</code> を <b>親staff_id</b> に更新します。<br><br>
                更新対象件数: <b>{target_count:,}</b> 件<br>
                対象売上合計: <b>¥ {target_amount:,}</b>
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.warning(
            "実行後は対象明細の帰属先が変わります。"
            "売上分析・給与計算の結果も変わるため、対象月をよく確認してから実行してください。"
        )

        final_check = st.checkbox(
            f"{year_month} の対象明細を親スタッフへ更新することを確認しました",
            value=False,
            key="baito_map_final_check",
        )

        confirm_col1, confirm_col2, confirm_col3 = st.columns([1.2, 1.6, 1.2])

        with confirm_col1:
            if st.button(
                "キャンセル",
                use_container_width=True,
                key="baito_map_cancel_confirm",
            ):
                st.session_state["baito_map_confirm_open"] = False
                st.rerun()

        with confirm_col2:
            if st.button(
                "最終実行：親スタッフへ一括マッピング",
                type="primary",
                disabled=not final_check,
                use_container_width=True,
                key="baito_map_execute_final",
            ):
                try:
                    affected = exec_baito_mapping_update_month(year_month)
                    st.session_state["baito_map_confirm_open"] = False
                    st.success(f"更新完了：{affected} 件の明細を親スタッフへ付け替えました。")
                    st.rerun()
                except Exception as e:
                    st.error(f"一括更新に失敗しました: {e}")
                    st.stop()

        with confirm_col3:
            st.caption("※ 実行後は一覧を再読込します")

        st.markdown("---")

        # フィルタ
        f1, f2, f3, f4 = st.columns([1.2, 1.3, 1.3, 1.6])
        with f1:
            show_mode = st.selectbox(
                "表示",
                ["全件", "親へマッピングのみ", "親未設定のみ", "親2あり（要確認）のみ", "対象外（ドリンクバック）のみ"],
                index=1,
                key="baito_map_show_mode",
            )
        with f2:
            kw_baito = st.text_input("検索（バイト名/ID）", "", key="baito_map_kw")
        with f3:
            kw_item = st.text_input("検索（メニュー/カテゴリ）", "", key="baito_map_item_kw")
        with f4:
            limit_map = st.selectbox("表示件数", [200, 500, 1000, 2000], index=1, key="baito_map_limit")

        filtered = df_map.copy()

        if show_mode == "親へマッピングのみ":
            filtered = filtered[filtered["mapping_status"] == "親へマッピング"]
        elif show_mode == "親未設定のみ":
            filtered = filtered[filtered["mapping_status"] == "親未設定"]
        elif show_mode == "親2あり（要確認）のみ":
            filtered = filtered[filtered["mapping_status"] == "親2あり（要確認）"]
        elif show_mode == "対象外（ドリンクバック）のみ":
            filtered = filtered[filtered["mapping_status"] == "対象外（ドリンクバック）"]

        if kw_baito.strip():
            k = kw_baito.strip().lower()
            filtered = filtered[
                filtered["baito_staff_id"].astype(str).str.lower().str.contains(k)
                | filtered["baito_staff_name"].astype(str).str.lower().str.contains(k)
            ]

        if kw_item.strip():
            k = kw_item.strip().lower()
            cols = [c for c in ["menu_name", "category_name"] if c in filtered.columns]
            if cols:
                mask = False
                for c in cols:
                    mask = mask | filtered[c].astype(str).str.lower().str.contains(k)
                filtered = filtered[mask]

        if "created_at" in filtered.columns:
            filtered = filtered.sort_values(["business_date", "created_at"], ascending=[False, False])

        filtered = filtered.head(int(limit_map))

        st.markdown("### 明細一覧")

        col_map = {
            "business_date": "営業日",
            "created_at": "日時",
            "order_id": "注文ID",
            "menu_name": "メニュー",
            "category_name": "カテゴリ",
            "qty": "数量",
            "unit_price": "単価",
            "line_total": "小計",
            "baito_staff_id": "現帰属ID",
            "baito_staff_name": "現帰属者（バイト）",
            "mapped_staff_id": "親staff_id",
            "mapped_staff_name": "親スタッフ名",
            "sub_parent_id": "親2",
            "mapping_status": "状態",
        }

        show_cols_raw = [
            "business_date",
            "created_at",
            "order_id",
            "menu_name",
            "category_name",
            "qty",
            "unit_price",
            "line_total",
            "baito_staff_id",
            "baito_staff_name",
            "mapped_staff_id",
            "mapped_staff_name",
            "sub_parent_id",
            "mapping_status",
        ]
        show_cols_raw = [c for c in show_cols_raw if c in filtered.columns]

        st.dataframe(
            filtered[show_cols_raw].rename(columns=col_map),
            use_container_width=True,
            hide_index=True,
        )

        csv_map = filtered.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "このマッピング一覧をCSVダウンロード",
            csv_map,
            file_name=f"baito_mapping_{year_month}.csv",
            use_container_width=True,
            key="baito_mapping_csv",
        )