import streamlit as st

def main():

    from services.staff_sync_service import StaffSyncService
    from repositories.staff_repository import StaffRepository
    from ui.ui_style import apply_global_style

    import sqlite3
    import pandas as pd

    apply_global_style()

    st.title("🧑‍🧑‍🧒‍🧒 担当者管理")
    tab1, tab2 = st.tabs(["担当者インポート", "担当者マスタ管理"])

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
            selected_id = st.radio(
                "スタッフ選択",
                options=[s.id for s in staff_list],
                format_func=lambda x: staff_dict[x].name,
                key="staff_selector"
            )

        # 切り替え時リロード
        if "last_selected_id" not in st.session_state:
            st.session_state.last_selected_id = selected_id

        if st.session_state.last_selected_id != selected_id:
            st.session_state.last_selected_id = selected_id
            st.rerun()

        selected_staff = staff_dict[selected_id]

        # -------------------------
        # 右：詳細編集
        # -------------------------
        with col_right:

            st.markdown(f"### 👤 {selected_staff.name} 詳細設定")
            st.write(f"タイプ：**{selected_staff.type}**")
            st.divider()

            # =============================
            # 親担当者
            # =============================
            parent_candidates = [
                s for s in staff_list if s.id != selected_staff.id
            ]
            id_name_map = {s.id: s.name for s in parent_candidates}
            parent_options = ["なし"] + list(id_name_map.keys())

            current_parents = selected_staff.parents or []
            parent1_default = current_parents[0] if len(current_parents) > 0 else "なし"
            parent2_default = current_parents[1] if len(current_parents) > 1 else "なし"

            col_p1, col_p2 = st.columns(2)

            with col_p1:
                parent1 = st.selectbox(
                    "メインサポート",
                    options=parent_options,
                    index=parent_options.index(parent1_default) if parent1_default in parent_options else 0,
                    format_func=lambda x: "なし" if x == "なし" else id_name_map[x],
                    key=f"parent1_{selected_id}"
                )

            with col_p2:
                filtered_options = [
                    opt for opt in parent_options
                    if opt == "なし" or opt != parent1
                ]

                parent2 = st.selectbox(
                    "サブサポート",
                    options=filtered_options,
                    index=filtered_options.index(parent2_default) if parent2_default in filtered_options else 0,
                    format_func=lambda x: "なし" if x == "なし" else id_name_map[x],
                    key=f"parent2_{selected_id}"
                )

            new_parents = []
            if parent1 != "なし":
                new_parents.append(parent1)
            if parent2 != "なし":
                new_parents.append(parent2)

            selected_staff.parents = new_parents

            st.divider()

            # =============================
            # 支払い方法
            # =============================
            payment_method = st.radio(
                "支払い方法",
                options=["cash", "bank", "stock"],
                format_func=lambda x: {
                    "cash": "手渡し",
                    "bank": "銀行振込",
                    "stock": "ストック"
                }[x],
                index=["cash","bank","stock"].index(
                    getattr(selected_staff, "payment_method", "bank")
                ),
                horizontal=True,
                key=f"payment_{selected_id}"
            )

            selected_staff.payment_method = payment_method

            if payment_method == "stock":
                st.success(f"現在のストック残高：{selected_staff.stock_balance:,} 円")

            st.divider()

            # =============================
            # バイト設定
            # =============================
            if selected_staff.type == "baito":

                selected_staff.hourly_wage = st.number_input(
                    "時給",
                    min_value=0,
                    value=getattr(selected_staff, "hourly_wage", 0),
                    key=f"hourly_{selected_id}"
                )

                selected_staff.working_hours = st.number_input(
                    "合計稼働時間",
                    min_value=0.0,
                    value=getattr(selected_staff, "working_hours", 0.0),
                    key=f"hours_{selected_id}"
                )

                selected_staff.transportation_cost = st.number_input(
                    "交通費（片道）",
                    min_value=0,
                    value=getattr(selected_staff, "transportation_cost", 0),
                    key=f"transport_{selected_id}"
                )

                selected_staff.work_days = st.number_input(
                    "出勤日数",
                    min_value=0,
                    value=getattr(selected_staff, "work_days", 0),
                    key=f"days_{selected_id}"
                )

                base_salary = selected_staff.hourly_wage * selected_staff.working_hours
                transport_total = selected_staff.transportation_cost * selected_staff.work_days * 2

                st.markdown("##### 💰 給与試算")
                st.write(f"時給分：{int(base_salary):,} 円")
                st.write(f"交通費合計：{int(transport_total):,} 円")
                st.success(f"合計：{int(base_salary + transport_total):,} 円")

            st.divider()

            # =============================
            # 銀行情報
            # =============================
            banks_df = get_bank_list()

            selected_bank_display = st.selectbox(
                "銀行（コード＋名称）",
                options=banks_df["display"],
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

                branches_df = get_branch_list(bank_code)

                selected_branch_display = st.selectbox(
                    "支店（コード＋名称）",
                    options=branches_df["display"],
                    key=f"branch_{selected_id}"
                )

                if selected_branch_display:
                    branch_code = selected_branch_display.split(" ")[0]
                    branch_name = selected_branch_display.split(" ", 1)[1]

                account_number_input = st.text_input(
                    "口座番号（7桁）",
                    key=f"account_{selected_id}"
                )

                account_number = "".join(filter(str.isdigit, account_number_input))
                if account_number:
                    account_number = account_number.zfill(7)

            account_type = st.selectbox(
                "口座種別",
                ["普通", "当座"],
                key=f"type_{selected_id}"
            )

            account_holder_kana = st.text_input(
                "口座名義（カナ）",
                key=f"holder_{selected_id}"
            )

            st.divider()

            if st.button("💾 保存", use_container_width=True):

                selected_staff.bank_code = bank_code
                selected_staff.bank_name = bank_name
                selected_staff.branch_code = branch_code
                selected_staff.branch_name = branch_name
                selected_staff.account_type = account_type
                selected_staff.account_number = account_number
                selected_staff.account_holder_kana = account_holder_kana

                StaffRepository.save(selected_staff)
                st.success("保存しました ✅")