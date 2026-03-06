from ui.ui_style import apply_global_style
from ui.sidebar import render_sidebar
apply_global_style()
render_sidebar()
import streamlit as st
import pandas as pd

from queries import q_staff_master_all, update_staff_master, q_banks, q_branches
if not st.session_state.get("authenticated", False):
    st.switch_page("app.py")
st.set_page_config(page_title="担当者メンテナンス", layout="wide")

# ===== CSS =====
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
  letter-spacing: 0.02em;
  line-height: 1.15;
  margin: 0 0 0.2rem 0;
  white-space: normal;
  word-break: break-word;
}
.subtle{ color: rgba(255,255,255,0.68); margin-bottom: 0.6rem; }
.section-title{
  font-size: 1.6rem;
  font-weight: 900;
  margin: 1.0rem 0 0.6rem 0;
  line-height: 1.15;
  white-space: normal;
  word-break: break-word;
}
.hint{ color: rgba(255,255,255,0.62); font-size: 0.92rem; }
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
hr{ border: none; border-top: 1px solid rgba(255,255,255,0.12); margin: 1.0rem 0; }
.card {
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 14px;
  padding: 1rem 1rem;
  background: rgba(255,255,255,0.03);
}
.small-muted { color: rgba(255,255,255,0.62); font-size: 0.86rem; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="big-title">👤担当者メンテナンス</div>', unsafe_allow_html=True)
st.markdown('<div class="subtle">担当者を選択して、詳細情報を編集・保存します</div>', unsafe_allow_html=True)
st.markdown("<hr/>", unsafe_allow_html=True)

# =========================================================
# Load
# =========================================================
df_all = q_staff_master_all().copy()

# 必要列保険
need_cols = [
    "staff_id", "name", "type", "parent_id", "parent_id_2",
    "hourly_wage", "transportation_allowance",
    "payment_method",
    "stock_amount",
    "bank_name", "bank_branch", "bank_account_type", "bank_account_number", "bank_account_holder",
]
for c in need_cols:
    if c not in df_all.columns:
        df_all[c] = None

df_all["staff_id"] = df_all["staff_id"].astype(str)
valid_ids = set(df_all["staff_id"].tolist())
id2name = {str(r["staff_id"]): str(r["name"]) for _, r in df_all.iterrows()}

def get_row_by_sid(sid: str) -> dict | None:
    hit = df_all[df_all["staff_id"].astype(str) == str(sid)]
    if hit.empty:
        return None
    return hit.iloc[0].to_dict()

# =========================================================
# Session init
# =========================================================
if "selected_staff_id" not in st.session_state:
    st.session_state.selected_staff_id = None
if "last_staff_id" not in st.session_state:
    st.session_state.last_staff_id = None

# =========================================================
# Tabs
# =========================================================
tab_edit, tab_tree = st.tabs(["メンテナンス", "担当者ツリー"])

# =========================================================
# Tab: Edit
# =========================================================
with tab_edit:
    left, right = st.columns([1.15, 1.85], gap="large")

    with left:
        st.markdown('<div class="section-title">担当者を選択<span class="badge">検索</span></div>', unsafe_allow_html=True)

        keyword = st.text_input("検索（名前 / staff_id）", "")
        type_filter = st.selectbox("種別フィルタ", ["すべて", "staff", "baito"])
        only_missing_bank = st.checkbox("銀行情報が未設定のみ", value=False)
        only_parent_issue = st.checkbox("親設定エラーのみ", value=False)

        df = df_all.copy()
        if keyword.strip():
            k = keyword.strip().lower()
            df = df[
                df["staff_id"].astype(str).str.lower().str.contains(k)
                | df["name"].astype(str).str.lower().str.contains(k)
            ]
        if type_filter != "すべて":
            df = df[df["type"] == type_filter]

        bank_cols = ["bank_name", "bank_branch", "bank_account_type", "bank_account_number", "bank_account_holder"]
        if only_missing_bank:
            mask = df[bank_cols].isna().any(axis=1) | (
                df[bank_cols].astype(str).apply(lambda s: s.str.strip()).eq("").any(axis=1)
            )
            df = df[mask]

        def has_parent_issue(r):
            sid = str(r["staff_id"])
            p1 = r.get("parent_id")
            p2 = r.get("parent_id_2")
            def bad(pid):
                if pid is None or str(pid).strip() == "":
                    return False
                pid = str(pid).strip()
                if pid == sid:
                    return True
                return pid not in valid_ids
            # 2親のどちらかが不正ならエラー
            if bad(p1) or bad(p2):
                return True
            # 2親が同じもエラー
            if p1 and p2 and str(p1).strip() != "" and str(p1).strip() == str(p2).strip():
                return True
            return False

        if only_parent_issue:
            df = df[df.apply(has_parent_issue, axis=1)]

        df = df.sort_values(["staff_id"])
        options = df.apply(lambda r: f"{r['staff_id']}｜{r['name']}（{r['type']}）", axis=1).tolist()

        # 現在選択ラベル（復元）
        current_sid = st.session_state.selected_staff_id
        current_label = ""
        if current_sid:
            r = get_row_by_sid(current_sid)
            if r:
                current_label = f"{r['staff_id']}｜{r['name']}（{r['type']}）"

        select_items = [""] + options
        default_index = select_items.index(current_label) if (current_label and current_label in select_items) else 0

        selected_label = st.selectbox("担当者", select_items, index=default_index, key="staff_picker")

        # ✅ 選択が変わったら即 rerun（右フォームの確実な切替）
        if selected_label == "":
            if st.session_state.selected_staff_id is not None:
                st.session_state.selected_staff_id = None
                st.rerun()
        else:
            new_sid = selected_label.split("｜")[0].strip()
            if st.session_state.selected_staff_id != new_sid:
                st.session_state.selected_staff_id = new_sid
                st.rerun()

        st.caption("一覧（参照用）")
        st.dataframe(
            df[["name", "type", "parent_id", "parent_id_2"]].rename(
                columns={"name": "名前", "type": "種別", "parent_id": "メイン", "parent_id_2": "サブ"}
            ),
            use_container_width=True,
            hide_index=True,
        )

    with right:
        st.markdown('<div class="section-title">詳細編集<span class="badge">フォーム</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="hint">左で担当者を選ぶと、ここに編集フォームが表示されます。</div>', unsafe_allow_html=True)
        st.markdown("<hr/>", unsafe_allow_html=True)

        sid = st.session_state.get("selected_staff_id")
        if not sid:
            st.info("左の一覧から担当者を選択してください。")
            st.stop()

        row_df = df_all[df_all["staff_id"].astype(str) == str(sid)]
        if row_df.empty:
            st.error("担当者データが見つかりません。")
            st.stop()
        row = row_df.iloc[0].to_dict()

        st.subheader(f"{row['staff_id']}｜{row['name']}")

        # -------------------------
        # 候補
        # -------------------------
        TYPE_LABELS = {"staff": "スタッフ", "baito": "バイト"}
        TYPE_VALUES = ["staff", "baito"]
        TYPE_DISPLAY = [TYPE_LABELS[v] for v in TYPE_VALUES]
        current_type = row.get("type") if row.get("type") in TYPE_VALUES else "staff"

        PAYMENT_METHOD_LABELS = {"cash": "手渡し（現金）", "bank": "銀行振込", "stock": "ストック"}
        pm_values = ["cash", "bank", "stock"]
        pm_labels = [PAYMENT_METHOD_LABELS[v] for v in pm_values]
        current_pm = (row.get("payment_method") or "cash")
        pm_index = pm_values.index(current_pm) if current_pm in pm_values else 0

        valid_ids = set(df_all["staff_id"].astype(str).tolist())
        id2name = {str(r["staff_id"]): str(r["name"]) for _, r in df_all.iterrows()}

        def label_for_pid(pid: str) -> str:
            if not pid:
                return ""
            return f"{pid}｜{id2name.get(pid, '')}"

        parent_ids = [""] + sorted([x for x in valid_ids if x != str(sid)])  # ✅ 自分を除外
        parent_labels = ["" if x == "" else label_for_pid(x) for x in parent_ids]

        def label_index(current_pid):
            current_pid = "" if current_pid is None else str(current_pid)
            return parent_ids.index(current_pid) if current_pid in parent_ids else 0

        # -------------------------
        # ✅ ここが肝：key を sid 付きにして “担当者ごと” にstateを分離する
        # -------------------------
        k_type   = f"staff_type_{sid}"
        k_main   = f"main_support_{sid}"
        k_sub    = f"sub_support_{sid}"
        k_pm     = f"payment_method_{sid}"

        k_bank_kw   = f"bank_kw_{sid}"
        k_bank_sel  = f"bank_sel_{sid}"
        k_branch_kw = f"branch_kw_{sid}"
        k_branch_sel= f"branch_sel_{sid}"

        k_bank_name   = f"bank_name_{sid}"
        k_branch_name = f"bank_branch_{sid}"
        k_bank_type   = f"bank_account_type_{sid}"
        k_bank_num    = f"bank_account_number_{sid}"
        k_bank_holder = f"bank_account_holder_{sid}"

        # -------------------------
        # フォーム（form自体も sid 付きにするとさらに安全）
        # -------------------------
        with st.form(key=f"staff_detail_form_{sid}", clear_on_submit=False):
            c1, c2, c3 = st.columns([1.2, 1.2, 1.6])

            with c1:
                type_disp = st.selectbox(
                    "種別",
                    TYPE_DISPLAY,
                    index=TYPE_VALUES.index(current_type),
                    key=k_type
                )
                staff_type = TYPE_VALUES[TYPE_DISPLAY.index(type_disp)]

                main_label = st.selectbox(
                    "メインサポート",
                    parent_labels,
                    index=label_index(row.get("parent_id")),
                    key=k_main
                )
                parent_id_1 = parent_ids[parent_labels.index(main_label)]

                payment_method_label = st.selectbox(
                    "支払い方法",
                    pm_labels,
                    index=pm_index,
                    key=k_pm
                )
                payment_method = pm_values[pm_labels.index(payment_method_label)]

            with c2:
                st.markdown("")
                st.markdown("")
                st.markdown("")
                st.markdown("")
                st.markdown("")
                sub_label = st.selectbox(
                    "サブサポート",
                    parent_labels,
                    index=label_index(row.get("parent_id_2")),
                    key=k_sub
                )
                parent_id_2 = parent_ids[parent_labels.index(sub_label)]

                st.markdown("")

                amt = int(row.get("stock_amount") or 0)
                st.markdown(
                    f"""
                    <div style="
                        margin: 0.7rem 0 1.0rem 0;
                        padding: 1.1rem 1.2rem;
                        border-radius: 14px;
                        background: rgba(60,255,122,0.10);
                        border: 1px solid rgba(60,255,122,0.20);
                        color: rgba(60,255,122,0.95);
                        font-weight: 900;
                        font-size: 1.15rem;
                    ">
                    現在のストック残高：{amt:,.0f} 円
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with c3:
                st.markdown("**銀行情報**")
                st.caption("銀行→支店を検索して選択し、口座情報を入力します。")

                # sid別キー
                k_bank_kw     = f"bank_kw_{sid}"
                k_bank_sel    = f"bank_sel_{sid}"
                k_branch_kw   = f"branch_kw_{sid}"
                k_branch_sel  = f"branch_sel_{sid}"
                k_acct_type   = f"bank_account_type_{sid}"
                k_acct_num    = f"bank_account_number_{sid}"
                k_acct_holder = f"bank_account_holder_{sid}"

                # --- 銀行検索/選択 ---
                bank_kw = st.text_input("銀行検索（コード/名称）", value="", key=k_bank_kw)
                banks_df = q_banks(bank_kw)
                bank_opts = [""] + [f"{r.bank_code}｜{r.bank_name}" for r in banks_df.itertuples()]

                current_bank_code = str(row.get("bank_code") or "").strip()
                bank_default = 0
                if current_bank_code:
                    for i, opt in enumerate(bank_opts):
                        if opt.startswith(current_bank_code + "｜"):
                            bank_default = i
                            break

                bank_sel = st.selectbox("銀行を選択", bank_opts, index=bank_default, key=k_bank_sel)

                picked_bank_code, picked_bank_name = "", ""
                if bank_sel:
                    picked_bank_code = bank_sel.split("｜")[0].strip()
                    picked_bank_name = bank_sel.split("｜")[1].strip()

                is_yucho = (picked_bank_code == "9900") or ("ゆうちょ" in (picked_bank_name or ""))

                # --- 支店検索/選択 ---
                branch_label = "支店検索（コード/名称）" if not is_yucho else "店名/店番検索（コード/名称）"
                branch_kw = st.text_input(branch_label, value="", key=k_branch_kw)

                branches_df = (
                    q_branches(picked_bank_code, branch_kw)
                    if picked_bank_code
                    else pd.DataFrame(columns=["branch_code", "branch_name"])
                )

                # 表示をゆうちょ寄せ（店番を前に）
                if is_yucho:
                    branch_opts = [""] + [f"{r.branch_code}｜{r.branch_name}" for r in branches_df.itertuples()]
                    branch_select_label = "店名（店番）を選択"
                else:
                    branch_opts = [""] + [f"{r.branch_code}｜{r.branch_name}" for r in branches_df.itertuples()]
                    branch_select_label = "支店を選択"

                current_branch_code = str(row.get("branch_code") or "").strip()
                branch_default = 0
                if picked_bank_code and current_branch_code:
                    for i, opt in enumerate(branch_opts):
                        if opt.startswith(current_branch_code + "｜"):
                            branch_default = i
                            break

                branch_sel = st.selectbox(
                    branch_select_label,
                    branch_opts,
                    index=branch_default,
                    key=k_branch_sel,
                    disabled=not bool(picked_bank_code),
                )

                picked_branch_code, picked_branch_name = "", ""
                if branch_sel:
                    picked_branch_code = branch_sel.split("｜")[0].strip()
                    picked_branch_name = branch_sel.split("｜")[1].strip()

                # --- 口座情報 ---
                # ゆうちょは通常「普通」扱いが多いので、UI上も寄せる（固定にしたければ下のコメント参照）
                acct_type_options = ["", "普通", "当座"]
                if is_yucho and (row.get("bank_account_type") or "") == "":
                    default_type = "普通"
                else:
                    default_type = (row.get("bank_account_type") or "")

                bank_type = st.selectbox(
                    "口座種別",
                    acct_type_options,
                    index=(acct_type_options.index(default_type) if default_type in acct_type_options else 0),
                    key=k_acct_type,
                )
                # 口座番号：ゆうちょは7桁が基本（銀行振込用）
                bank_number = st.text_input("口座番号", value=row.get("bank_account_number") or "", key=k_acct_num)
                bank_holder = st.text_input("口座名義", value=row.get("bank_account_holder") or "", key=k_acct_holder)

                # --- ゆうちょ簡易バリデーション（強制ではない） ---
                if is_yucho:
                    # 数字以外除去して警告（必要なら自動整形にしてもOK）
                    num_only = "".join(ch for ch in str(bank_number) if ch.isdigit())
                    if bank_number and bank_number != num_only:
                        st.warning("ゆうちょの口座番号は数字のみで入力してください（振込用は通常7桁）。")
                    if num_only and len(num_only) != 7:
                        st.info("ゆうちょの振込用口座番号は通常 7桁 です。")

                # 保存で使う値（payloadで参照）
                st.session_state[f"_picked_bank_code_{sid}"] = picked_bank_code or None
                st.session_state[f"_picked_bank_name_{sid}"] = picked_bank_name or None
                st.session_state[f"_picked_branch_code_{sid}"] = picked_branch_code or None
                st.session_state[f"_picked_branch_name_{sid}"] = picked_branch_name or None

            st.markdown("<hr/>", unsafe_allow_html=True)

            # 事前チェック
            errs = []
            if parent_id_1 and parent_id_1 not in valid_ids:
                errs.append("親ID①が存在しません。")
            if parent_id_1 and parent_id_1 == str(sid):
                errs.append("親ID①に自分自身は設定できません。")
            if parent_id_2 and parent_id_2 not in valid_ids:
                errs.append("親ID②が存在しません。")
            if parent_id_2 and parent_id_2 == str(sid):
                errs.append("親ID②に自分自身は設定できません。")
            if parent_id_2 and parent_id_2 == parent_id_1 and parent_id_2 != "":
                errs.append("親ID①と親ID②が同じです。")

            if errs:
                st.warning("入力チェック：要確認\n\n" + "\n".join([f"・{e}" for e in errs]))

            save = st.form_submit_button("保存", type="primary", use_container_width=True)

        # ---- 保存（フォーム外）----
        if save:
            payload = {
                "staff_id": str(sid),
                "type": staff_type,
                "parent_id": (None if not parent_id_1 else parent_id_1),
                "parent_id_2": (None if not parent_id_2 else parent_id_2),
                "bank_code": st.session_state.get(f"_picked_bank_code_{sid}"),
                "branch_code": st.session_state.get(f"_picked_branch_code_{sid}"),
                "bank_name": st.session_state.get(f"_picked_bank_name_{sid}"),
                "bank_branch": st.session_state.get(f"_picked_branch_name_{sid}"),
                "bank_account_type": (bank_type.strip() or None),
                "bank_account_number": (bank_number.strip() or None),
                "bank_account_holder": (bank_holder.strip() or None),
                "payment_method": payment_method,

                # ✅ bank_code/branch_code をDBに保存したいなら update_staff_master を拡張してここも送る
                "bank_code": st.session_state.get(f"bank_code_{sid}"),
                "branch_code": st.session_state.get(f"branch_code_{sid}"),
            }

            update_staff_master(payload)
            st.success("保存しました。")
            #st.rerun()

# =========================================================
# Tab: Tree
# =========================================================
with tab_tree:
    import streamlit as st
    import pandas as pd

    def _norm(x) -> str:
        if x is None:
            return ""
        s = str(x).strip()
        if s.lower() == "none":
            return ""
        return s

    def build_org_dot(df_all: pd.DataFrame, *, type_filter: str="all", highlight_sid: str|None=None) -> str:
        df = df_all.copy()
        for col in ["staff_id", "name", "type", "parent_id", "parent_id_2"]:
            if col not in df.columns:
                df[col] = None

        df["staff_id"] = df["staff_id"].astype(str)
        df["name"] = df["name"].astype(str)
        df["type"] = df["type"].astype(str)

        if type_filter in ["staff", "baito"]:
            df = df[df["type"] == type_filter]

        ids = set(df["staff_id"].tolist())

        # DOT
        dot = []
        dot.append("digraph G {")
        dot.append('  rankdir=TB;')  # 上→下
        dot.append('  bgcolor="transparent";')
        dot.append('  graph [splines=true, nodesep=0.28, ranksep=0.45, concentrate=true];')

        # ノード：ダークでも見やすい
        dot.append('  node [shape=ellipse, style="filled", fontname="Helvetica", fontsize=14, penwidth=2.2];')
        # エッジ：濃く、メイン/サブで差
        dot.append('  edge [color="#0B1220", arrowsize=0.9, penwidth=2.0];')

        # タイプ別の色（淡色×濃枠でコントラスト）
        STAFF_FILL = "#E8F0FF"   # 淡い青
        STAFF_BORDER = "#1D4ED8" # 濃い青
        BAITO_FILL = "#ECFDF5"   # 淡い緑
        BAITO_BORDER = "#16A34A" # 濃い緑
        FONT_COLOR = "#0B1220"   # ほぼ黒

        # ノード生成
        for r in df.to_dict("records"):
            sid = r["staff_id"]
            name = r["name"]
            tp = r.get("type") or "staff"

            label = f"{name}\\n({sid})"

            if tp == "baito":
                fill = BAITO_FILL
                border = BAITO_BORDER
            else:
                fill = STAFF_FILL
                border = STAFF_BORDER

            # ハイライト
            if highlight_sid and sid == str(highlight_sid):
                dot.append(
                    f'  "{sid}" [label="{label}", fillcolor="{fill}", color="#F97316", fontcolor="{FONT_COLOR}", penwidth=3.8];'
                )
            else:
                dot.append(
                    f'  "{sid}" [label="{label}", fillcolor="{fill}", color="{border}", fontcolor="{FONT_COLOR}"];'
                )

        # エッジ（親→子）
        for r in df.to_dict("records"):
            child = r["staff_id"]
            p1 = _norm(r.get("parent_id"))
            p2 = _norm(r.get("parent_id_2"))

            # メイン親：太線・グレー
            if p1 and p1 in ids and child in ids and p1 != child:
                dot.append(f'  "{p1}" -> "{child}" [penwidth=2.8, color="#6B7280"];')

            # サブ親：点線・グレー
            if p2 and p2 in ids and child in ids and p2 != child:
                dot.append(f'  "{p2}" -> "{child}" [style=dashed, penwidth=2.2, color="#6B7280"];')

        dot.append("}")
        return "\n".join(dot)

    # ===== 組織図タブ内 =====
    st.subheader("組織図")

    c1, c2, c3 = st.columns([1.1, 1.1, 1.8])
    with c1:
        tf = st.selectbox("表示フィルタ", ["all", "staff", "baito"], index=0, key="org_tf")
    with c2:
        highlight_sid = st.text_input("ハイライト staff_id（任意）", value="", key="org_hi").strip() or None
    with c3:
        st.caption("凡例：青=staff / 緑=baito　太線=メイン親 / 点線=サブ親")

    dot = build_org_dot(df_all, type_filter=tf, highlight_sid=highlight_sid)
    st.graphviz_chart(dot, use_container_width=True)