import streamlit as st
from services.staff_sync_service import StaffSyncService
from repositories.staff_repository import StaffRepository

from ui.ui_style import apply_global_style
apply_global_style()

st.markdown('<div class="sticky-header">', unsafe_allow_html=True)
st.title("🧑‍🧑‍🧒‍🧒 担当者管理")
st.markdown('</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["担当者インポート", "担当者マスタ管理"])

import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = "app.db"

def get_connection():
    return sqlite3.connect(DB_PATH)


def get_bank_list():
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT bank_code, bank_name FROM banks ORDER BY bank_code",
        conn
    )
    conn.close()

    df["display"] = df["bank_code"] + " " + df["bank_name"]
    return df


def get_branch_list(bank_code):
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT branch_code, branch_name
        FROM branches
        WHERE bank_code = ?
        ORDER BY branch_code
        """,
        conn,
        params=[bank_code]
    )
    conn.close()

    df["display"] = df["branch_code"] + " " + df["branch_name"]
    return df

# =============================
# インポート
# =============================
with tab1:
    uploaded_file = st.file_uploader("POSスタッフCSV取込", type="csv")

    if uploaded_file:
        StaffSyncService.sync_from_pos(uploaded_file)
        st.success("担当者同期完了")

# =============================
# マスタ管理
# =============================
with tab2:

    staff_list = StaffRepository.load_all()

    if not staff_list:
        st.warning("スタッフ未登録")
        st.stop()

    staff_dict = {s.id: s for s in staff_list}

    col_left, col_right = st.columns([1, 2])

    # -------------------------
    # 左：スタッフ選択
    # -------------------------
    with col_left:
        st.subheader("スタッフ一覧")

        selected_id = st.radio(
            "選択",
            options=[s.id for s in staff_list],
            format_func=lambda x: f"{staff_dict[x].name}"
        )

    selected_staff = staff_dict[selected_id]
    if "last_selected_id" not in st.session_state:
        st.session_state.last_selected_id = selected_id

    if st.session_state.last_selected_id != selected_id:
        st.session_state.clear()
        st.session_state.last_selected_id = selected_id
        st.rerun()

    # -------------------------
    # 右：詳細編集
    # -------------------------
    with col_right:

        st.markdown(f"### 👤 {selected_staff.name}　詳細設定")
        st.write(f"タイプ：**{selected_staff.type}**")

        st.divider()

        # =============================
        # 親担当者
        # =============================
        st.markdown("#### ■ 親担当者設定")

        parent_candidates = [
            s for s in staff_list if s.id != selected_staff.id
        ]

        id_name_map = {s.id: s.name for s in parent_candidates}

        # =============================
        # 親担当者（最大2人）
        # =============================

        parent_candidates = [
            s for s in staff_list if s.id != selected_staff.id
        ]

        id_name_map = {s.id: s.name for s in parent_candidates}

        parent_options = ["なし"] + list(id_name_map.keys())

        # 既存値を安全に取得
        current_parents = selected_staff.parents or []

        parent1_default = current_parents[0] if len(current_parents) > 0 else "なし"
        parent2_default = current_parents[1] if len(current_parents) > 1 else "なし"

        col_p1, col_p2 = st.columns(2)

        with col_p1:
            parent1 = st.selectbox(
                "メインサポート",
                options=parent_options,
                index=parent_options.index(parent1_default) if parent1_default in parent_options else 0,
                format_func=lambda x: "なし" if x == "なし" else id_name_map[x]
            )

        with col_p2:
            # ①と同じ人は選べないように制御
            filtered_options = [
                opt for opt in parent_options
                if opt == "なし" or opt != parent1
            ]

            parent2 = st.selectbox(
                "サブサポート",
                options=filtered_options,
                index=filtered_options.index(parent2_default) if parent2_default in filtered_options else 0,
                format_func=lambda x: "なし" if x == "なし" else id_name_map[x]
            )

        # 保存用リスト生成（従来形式維持）
        new_parents = []

        if parent1 != "なし":
            new_parents.append(parent1)

        if parent2 != "なし":
            new_parents.append(parent2)

        selected_staff.parents = new_parents


        st.divider()

        # =============================
        # バイト給与設定
        # =============================
        st.markdown("#### ■ バイト給与設定")

        if selected_staff.type == "baito":

            selected_staff.hourly_wage = st.number_input(
                "時給",
                min_value=0,
                value=getattr(selected_staff, "hourly_wage", 0)
            )

            selected_staff.working_hours = st.number_input(
                "合計稼働時間",
                min_value=0.0,
                value=selected_staff.working_hours
            )

            selected_staff.transportation_cost = st.number_input(
                "交通費（片道）",
                min_value=0,
                value=selected_staff.transportation_cost
            )

            selected_staff.work_days = st.number_input(
                "出勤日数",
                min_value=0,
                value=getattr(selected_staff, "work_days", 0)
            )

            base_salary = selected_staff.hourly_wage * selected_staff.working_hours
            transport_total = selected_staff.transportation_cost * selected_staff.work_days * 2

            st.markdown("##### 💰 給与試算")
            st.write(f"時給分：{int(base_salary):,} 円")
            st.write(f"交通費合計：{int(transport_total):,} 円")
            st.success(f"合計：{int(base_salary + transport_total):,} 円")

        else:
            st.number_input("時給", value=0, disabled=True)
            st.number_input("合計稼働時間", value=0.0, disabled=True)
            st.number_input("交通費（片道）", value=0, disabled=True)
            st.number_input("出勤日数", value=0, disabled=True)

        st.divider()

        # =============================
        # 銀行口座情報
        # =============================
        st.markdown("## 振込先情報")

        banks_df = get_bank_list()

        selected_bank_display = st.selectbox(
            "銀行（コード＋名称）",
            options=banks_df["display"],
            index=None,
            key=f"bank_{selected_id}"
        )

        bank_code = None
        bank_name = None
        branch_code = None
        branch_name = None
        account_number = None

        if selected_bank_display:
            bank_code = selected_bank_display.split(" ")[0]
            bank_name = selected_bank_display.split(" ", 1)[1]

            st.text_input("銀行コード", value=bank_code, disabled=True)

            is_yucho = (bank_code == "9900")

            # =============================
            # 🔵 ゆうちょの場合
            # =============================
            if is_yucho:

                st.info("ゆうちょは記号・番号を入力してください")

                yucho_symbol = st.text_input(
                    "記号（5桁）",
                    key=f"yucho_symbol_{selected_id}"
                )

                yucho_number = st.text_input(
                    "番号（最大8桁）",
                    key=f"yucho_number_{selected_id}"
                )

                yucho_symbol = "".join(filter(str.isdigit, yucho_symbol))
                yucho_number = "".join(filter(str.isdigit, yucho_number))

                # 店番生成
                if len(yucho_symbol) == 5:
                    branch_code = yucho_symbol[1:4]
                    branch_name = f"{branch_code}店"

                # 口座番号変換（🔥重要）
                if len(yucho_number) >= 7:
                    account_number = yucho_number[-7:]  # 下7桁取得

            # =============================
            # 🟢 通常銀行
            # =============================
            else:

                branches_df = get_branch_list(bank_code)

                selected_branch_display = st.selectbox(
                    "支店（コード＋名称）",
                    options=branches_df["display"],
                    index=None,
                    key=f"branch_{selected_id}"
                )

                if selected_branch_display:
                    branch_code = selected_branch_display.split(" ")[0]
                    branch_name = selected_branch_display.split(" ", 1)[1]

                    st.text_input("支店コード", value=branch_code, disabled=True)

                account_number_input = st.text_input(
                    "口座番号（7桁）",
                    key=f"account_{selected_id}"
                )

                account_number = "".join(filter(str.isdigit, account_number_input))

                if account_number:
                    account_number = account_number.zfill(7)
                    st.text_input("ゼロ埋め後口座番号", value=account_number, disabled=True)

        # =============================
        # 共通項目
        # =============================

        account_type = st.selectbox(
            "口座種別",
            ["普通", "当座"],
            key=f"account_type_{selected_id}"
        )

        account_holder_kana = st.text_input(
            "口座名義（全角カナ）",
            key=f"account_holder_{selected_id}"
        )


        st.divider()

        # =============================
        # 保存ボタン
        # =============================
        if st.button("💾 保存", use_container_width=True):

            if not bank_code:
                st.error("銀行を選択してください")

            elif not branch_code:
                st.error("支店情報が不足しています")

            elif not account_number or len(account_number) != 7:
                st.error("口座番号は7桁である必要があります")

            elif not account_holder_kana:
                st.error("口座名義（カナ）を入力してください")

            else:
                # 🔥 スタッフへセット
                selected_staff.bank_code = bank_code
                selected_staff.bank_name = bank_name
                selected_staff.branch_code = branch_code
                selected_staff.branch_name = branch_name
                selected_staff.account_type = account_type
                selected_staff.account_number = account_number
                selected_staff.account_holder_kana = account_holder_kana

                # 🔥 保存
                StaffRepository.save(selected_staff)

                st.success("保存しました ✅")