from ui.ui_style import apply_global_style
apply_global_style()

from ui.sidebar import render_sidebar
render_sidebar()
import streamlit as st
import pandas as pd
import uuid
from queries import q_rate_rules, exec_sql
from queries import q_categories, update_category
from db import fetch_all  
from db import fetch_one  


st.set_page_config(page_title="給与ルール管理", layout="wide")

st.markdown(
"""
<style>
/* Deploy帯に被らないように「中身のコンテナ」を下げる（安定） */
.block-container{
  padding-top: 4.2rem !important;   /* ここで確実に下げる */
  padding-left: 1.2rem;
  padding-right: 1.2rem;
  max-width: 1400px;
}

/* 見出し */
.big-title{
  font-size: 2.2rem;
  font-weight: 900;
  letter-spacing: 0.02em;
  line-height: 1.15;
  margin: 0 0 0.2rem 0;
  white-space: normal;
  word-break: break-word;
}
.subtle{ color: rgba(255,255,255,0.68); margin-bottom: 0.6rem; }
.section-title{ font-size: 1.6rem; font-weight: 900; margin: 1.0rem 0 0.6rem 0; line-height: 1.15; white-space: normal; word-break: break-word; }
.hint{ color: rgba(255,255,255,0.62); font-size: 0.92rem; }
.badge{ display:inline-block; padding: 0.12rem 0.6rem; border-radius: 999px; background: rgba(60,255,122,0.14); color: rgba(60,255,122,0.95); font-weight: 800; font-size: 0.85rem; margin-left: 0.4rem; vertical-align: middle;}
hr{ border: none; border-top: 1px solid rgba(255,255,255,0.12); margin: 1.0rem 0; }
</style>
""",
unsafe_allow_html=True
)

st.markdown('<div class="big-title">💹給与ルール管理</div>', unsafe_allow_html=True)
st.markdown('<div class="subtle">POSと連動した給与計算ルールを管理します</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["売上報酬F管理", "カテゴリ別F管理", "ストック残高調整"])

with tab1:
    st.markdown('<div class="section-title">組織売上Fに応じた報酬レート<span class="badge">適用レート</span></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hint">下限〜上限の範囲に「組織売上（org_sales）」が入ったときに、報酬率（rate）が適用されます。上限が空欄の行は「上限なし」扱いです。</div>',
        unsafe_allow_html=True
    )
    st.markdown("<hr/>", unsafe_allow_html=True)

    df = q_rate_rules().copy()
    if not df.empty:
        df["rate_percent"] = (pd.to_numeric(df["rate"], errors="coerce").fillna(0) * 100).round(2)
    else:
        df = pd.DataFrame(columns=["rule_id", "min_amount", "max_amount", "rate", "is_active", "sort_order", "rate_percent"])

    # 内部IDはUIに出さない（_rule_idとして保持）
    ui_df = df[["rule_id", "min_amount", "max_amount", "rate_percent", "is_active", "sort_order"]].rename(columns={
        "rule_id": "_rule_id",
        "min_amount": "下限F",
        "max_amount": "上限F",
        "rate_percent": "報酬率(%)",
        "is_active": "有効",
        "sort_order": "並び順",
    })

    ui_view = ui_df.drop(columns=["_rule_id"])

    edited_view = st.data_editor(
        ui_view,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        column_config={
            "下限F": st.column_config.NumberColumn("下限F", step=1, format="%d"),
            "上限F": st.column_config.NumberColumn("上限F", step=1, format="%d", help="空欄 = 上限なし"),
            "報酬率(%)": st.column_config.NumberColumn("報酬率(%)", step=0.1, format="%.2f"),
            "有効": st.column_config.CheckboxColumn("有効"),
            "並び順": st.column_config.NumberColumn("並び順", step=1, format="%d"),
        },
    )

    # rule_id復元（新規行はUUIDを割当）
    base_ids = ui_df["_rule_id"].tolist()
    needed = len(edited_view) - len(base_ids)
    if needed > 0:
        base_ids += [str(uuid.uuid4()) for _ in range(needed)]

    edited = edited_view.copy()
    edited.insert(0, "rule_id", base_ids[: len(edited_view)])

    colA, colB, colC = st.columns([2, 2, 3])
    with colA:
        st.caption("✅ ルール整合性チェック")
        check_btn = st.button("チェック", use_container_width=True)
    with colB:
        st.caption("💾 DBに保存")
        save_btn = st.button("売上報酬Fを保存", type="primary", use_container_width=True)
    with colC:
        st.caption("ℹ️ 注意")
        st.write(
            "- 範囲が重なる/穴があると、レートが当たらないケースが出ます\n"
            "- MVPは「穴があったら警告」でOK（運用で直す）\n"
            "- 将来的に「自動整形」も追加できます"
        )

    def normalize(d: pd.DataFrame) -> pd.DataFrame:
        x = d.copy()
        x["下限F"] = pd.to_numeric(x["下限F"], errors="coerce").fillna(0).astype(int)
        x["上限F"] = pd.to_numeric(x["上限F"], errors="coerce")  # NaN OK
        x["報酬率(%)"] = pd.to_numeric(x["報酬率(%)"], errors="coerce").fillna(0.0)
        x["並び順"] = pd.to_numeric(x["並び順"], errors="coerce").fillna(0).astype(int)
        x["有効"] = x["有効"].fillna(True).astype(bool)
        x["rate"] = (x["報酬率(%)"] / 100.0).round(6)
        return x

    def check_ranges(x: pd.DataFrame) -> list[str]:
        v = x[x["有効"] == True].copy()
        if v.empty:
            return ["有効なルールが0件です。最低1件は有効にしてください。"]

        v = v.sort_values(["下限F", "並び順"]).reset_index(drop=True)
        msgs: list[str] = []

        for i, r in v.iterrows():
            lo = int(r["下限F"])
            hi = r["上限F"]
            if pd.notna(hi) and int(hi) < lo:
                msgs.append(f"行{i+1}: 上限F({int(hi)})が下限F({lo})より小さいです。")

        prev_max = None
        for i, r in v.iterrows():
            lo = int(r["下限F"])
            hi = r["上限F"]

            if prev_max is not None:
                # 穴：prev_max+1 より大きいときだけ
                if lo > prev_max + 1:
                    msgs.append(f"穴があります: 前の上限F({prev_max}) < 次の下限F({lo})")
                # 重なり：上限を含むなら lo<=prev_max が重なり
                if lo <= prev_max:
                    msgs.append(f"範囲が重なっています: 次の下限F({lo}) <= 前の上限F({prev_max})")

            if pd.isna(hi):
                if i != len(v) - 1:
                    msgs.append("上限なし（空欄）の行が途中にあります。上限なしは最後の行にしてください。")
                break

            prev_max = int(hi)

        bad = v[(v["報酬率(%)"] < 0) | (v["報酬率(%)"] > 100)]
        if not bad.empty:
            msgs.append("報酬率(%)は 0〜100 の範囲にしてください。")

        return msgs

    normalized = normalize(edited)

    if check_btn:
        msgs = check_ranges(normalized)
        if msgs:
            st.warning("チェック結果：要確認")
            for m in msgs:
                st.write("•", m)
        else:
            st.success("OK：大きな問題は見つかりませんでした。")

    if save_btn:
        msgs = check_ranges(normalized)
        if msgs:
            st.warning("保存はできますが、後で給与計算でレート未適用が出る可能性があります。")
            for m in msgs:
                st.write("•", m)

        for _, r in normalized.iterrows():
            exec_sql(
                """
                insert into rate_rules (rule_id, min_amount, max_amount, rate, is_active, sort_order)
                values (%s,%s,%s,%s,%s,%s)
                on conflict (rule_id)
                do update set
                  min_amount = excluded.min_amount,
                  max_amount = excluded.max_amount,
                  rate = excluded.rate,
                  is_active = excluded.is_active,
                  sort_order = excluded.sort_order
                """,
                [
                    str(r["rule_id"]),
                    int(r["下限F"]),
                    (None if pd.isna(r["上限F"]) else int(r["上限F"])),
                    float(r["rate"]),
                    bool(r["有効"]),
                    int(r["並び順"]),
                ],
            )

        st.success("保存しました。")
        st.rerun()
with tab2:
    st.markdown('<div class="section-title">カテゴリ別F管理<span class="badge">f_rate / drink back</span></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hint">カテゴリごとの F率（f_rate）と、ドリンクバック対象（is_drink_back）を編集します。</div>',
        unsafe_allow_html=True
    )
    st.markdown("<hr/>", unsafe_allow_html=True)

    # ------- Filter UI -------
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        keyword = st.text_input("検索（カテゴリ名 / ID）", "")
    with col2:
        only_drink = st.checkbox("ドリンクバック対象のみ", value=False)
    with col3:
        show_changed_only = st.checkbox("変更行のみ表示", value=False)

    df = q_categories().copy()

    # ------- Apply filters -------
    if keyword.strip():
        k = keyword.strip().lower()
        df = df[
            df["category_id"].astype(str).str.lower().str.contains(k)
            | df["name"].astype(str).str.lower().str.contains(k)
        ]

    if only_drink:
        df = df[df["is_drink_back"] == True]

    # ------- Editor -------
    base = df.copy()
    edited = st.data_editor(
        df,
        use_container_width=True,
        num_rows="fixed",
        hide_index=True,
        column_config={
            "category_id": st.column_config.TextColumn("category_id", disabled=True),
            "name": st.column_config.TextColumn("カテゴリ名", disabled=True),
            "f_rate": st.column_config.NumberColumn("f_rate", step=0.01, format="%.4f"),
            "is_drink_back": st.column_config.CheckboxColumn("ドリンクバック対象"),
        },
    )

    # ------- Diff detect -------
    merged = base.merge(edited, on="category_id", suffixes=("_old", "_new"))
    changed = merged[
        (merged["f_rate_old"] != merged["f_rate_new"])
        | (merged["is_drink_back_old"] != merged["is_drink_back_new"])
    ].copy()

    if show_changed_only:
        if changed.empty:
            st.info("変更された行はまだありません。")
        else:
            preview = changed[["category_id", "name_old", "f_rate_old", "f_rate_new", "is_drink_back_old", "is_drink_back_new"]].rename(columns={
                "name_old": "カテゴリ名",
                "f_rate_old": "f_rate(元)",
                "f_rate_new": "f_rate(新)",
                "is_drink_back_old": "drink(元)",
                "is_drink_back_new": "drink(新)",
            })
            st.dataframe(preview, use_container_width=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    colA, colB, colC = st.columns([2, 2, 3])
    with colA:
        st.caption("✅ 簡易チェック")
        if st.button("チェック（f_rate範囲）", use_container_width=True):
            bad = edited[(edited["f_rate"] < 0) | (edited["f_rate"] > 1)]
            if bad.empty:
                st.success("OK：f_rate は 0〜1 の範囲です。")
            else:
                st.warning("f_rate が 0〜1 の範囲外の行があります。")
                st.dataframe(bad[["category_id","name","f_rate"]], use_container_width=True)

    with colB:
        st.caption("💾 DBに保存")
        if st.button("カテゴリFを保存", type="primary", use_container_width=True):
            for _, r in changed.iterrows():
                update_category(r["category_id"], r["f_rate_new"], r["is_drink_back_new"])
            st.success(f"保存しました（{len(changed)}件）")
            st.rerun()

    with colC:
        st.caption("ℹ️ ヒント")
        st.write(
            "- f_rate は **0〜1**（例：0.55）\n"
            "- ドリンクバック対象は **is_drink_back** をON\n"
            "- 変更は差分だけ保存されます"
        )

with tab3:
    st.subheader("🏦 ストック残高調整（初期値設定 / 手動調整）")
    st.caption("運用途中から導入する場合の初期ストック設定や、誤差調整に使用します。")

    # ==========
    # ヘルパ（このtab内だけで完結させる）
    # ==========
    def table_exists(table_name: str, schema: str = "public") -> bool:
        row = fetch_one(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = %(schema)s
              AND table_name = %(table)s
              AND table_type = 'BASE TABLE'
            LIMIT 1
            """,
            {"schema": schema, "table": table_name},
        )
        return bool(row)

    def safe_int(v, default=0) -> int:
        try:
            if v is None:
                return default
            return int(float(str(v).strip()))
        except Exception:
            return default

    # ==========
    # スタッフ一覧取得
    # ==========
    colL, colR = st.columns([2, 1])
    with colL:
        keyword = st.text_input("検索（スタッフ名）", value="", placeholder="例：山田 / yama")
    with colR:
        type_filter = st.selectbox("対象タイプ", ["全員", "staffのみ", "baitoのみ"], index=0)

    where = []
    params = {}

    if keyword.strip():
        where.append("(name ILIKE %(kw)s)")
        params["kw"] = f"%{keyword.strip()}%"

    if type_filter == "staffのみ":
        where.append("type = 'staff'")
    elif type_filter == "baitoのみ":
        where.append("type = 'baito'")

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    staff_rows = fetch_all(
        f"""
        SELECT staff_id, name, type, payment_method, COALESCE(stock_amount,0) AS stock_amount
        FROM public.staff
        {where_sql}
        ORDER BY type, name
        """,
        params,
    )

    if not staff_rows:
        st.info("対象スタッフがいません。検索条件を確認してください。")
        st.stop()

    # 表示用ラベル
    options = {
        r["staff_id"]: f"[{r['type']}] {r['name']}（{r.get('payment_method') or '-'}） / 現在ストック: ¥{safe_int(r['stock_amount']):,}"
        for r in staff_rows
    }

    st.divider()

    # ==========
    # 個別調整
    # ==========
    st.markdown("### 個別調整")
    staff_id = st.selectbox(
        "対象スタッフ",
        options=list(options.keys()),
        format_func=lambda sid: options.get(sid, str(sid)),
    )

    current = fetch_one(
        """
        SELECT staff_id, name, type, payment_method, COALESCE(stock_amount,0) AS stock_amount
        FROM public.staff
        WHERE staff_id = %(sid)s
        """,
        {"sid": staff_id},
    )

    if not current:
        st.error("スタッフが見つかりません。")
        st.stop()

    current_stock = safe_int(current["stock_amount"])
    st.write(f"**現在のストック残高：¥{current_stock:,}**")

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        mode = st.selectbox("調整方法", ["初期値として上書き", "加算する", "減算する"], index=0)
    with c2:
        amount = st.number_input("金額（円）", min_value=0, step=1000, value=0)
    with c3:
        note = st.text_input("メモ（任意）", value="", placeholder="例：運用開始時の初期ストック / 誤差調整 / 手動補正 など")

    # 反映後の見込み
    amt = safe_int(amount)
    if mode == "初期値として上書き":
        next_stock = amt
        delta = next_stock - current_stock
    elif mode == "加算する":
        next_stock = current_stock + amt
        delta = amt
    else:  # 減算する
        next_stock = max(0, current_stock - amt)  # マイナスにしたくないなら0で下限
        delta = next_stock - current_stock

    st.write(f"➡️ 反映後：**¥{next_stock:,}**（差分：{delta:+,}円）")

    warn_cols = []
    if mode == "減算する" and amt > current_stock:
        warn_cols.append("減算額が現在残高を超えています（0円に丸めます）")
    if amt == 0 and mode != "初期値として上書き":
        warn_cols.append("金額が0円です（更新しても変化しません）")
    if warn_cols:
        st.warning(" / ".join(warn_cols))

    # ==========
    # 監査ログ（任意）
    # ==========
    # あれば書く：public.stock_adjust_logs
    # 推奨カラム例：
    # log_id uuid default gen_random_uuid()
    # staff_id uuid
    # target_month text null（必要なら）
    # before_amount int
    # delta int
    # after_amount int
    # note text
    # created_at timestamptz default now()
    has_log = table_exists("stock_adjust_logs")

    # ==========
    # 実行
    # ==========
    colA, colB = st.columns([1, 2])
    with colA:
        do_update = st.button("✅ 反映する", type="primary", use_container_width=True)
    with colB:
        st.caption("※ 反映後は即時に staff.stock_amount が更新されます。")

    if do_update:
        # 念のため最新を取り直して衝突を避ける
        latest = fetch_one(
            "SELECT COALESCE(stock_amount,0) AS stock_amount FROM public.staff WHERE staff_id=%(sid)s",
            {"sid": staff_id},
        )
        latest_stock = safe_int((latest or {}).get("stock_amount", 0))

        # 最新値から再計算（ボタン押す直前に変わってた時の事故防止）
        if mode == "初期値として上書き":
            after = amt
            delta2 = after - latest_stock
        elif mode == "加算する":
            after = latest_stock + amt
            delta2 = amt
        else:
            after = max(0, latest_stock - amt)
            delta2 = after - latest_stock

        exec_sql(
            """
            UPDATE public.staff
            SET stock_amount = %(after)s
            WHERE staff_id = %(sid)s
            """,
            {"after": after, "sid": staff_id},
        )

        if has_log:
            # ログテーブルがあるなら記録（なければスルー）
            exec_sql(
                """
                INSERT INTO public.stock_adjust_logs
                  (staff_id, before_amount, delta, after_amount, note, created_at)
                VALUES
                  (%(sid)s, %(before)s, %(delta)s, %(after)s, %(note)s, now())
                """,
                {
                    "sid": staff_id,
                    "before": latest_stock,
                    "delta": delta2,
                    "after": after,
                    "note": note.strip(),
                },
            )

        st.success(f"反映しました：¥{latest_stock:,} → ¥{after:,}（{delta2:+,}円）")
        st.rerun()

    st.divider()