# pages/transfer_page.py
def main():
    import streamlit as st
    from datetime import datetime
    import pandas as pd

    from repositories.staff_repository import StaffRepository
    from repositories.salary_confirm_repository import SalaryConfirmRepository
    from ui.ui_style import apply_global_style

    apply_global_style()
    st.title("🏦 振込データ出力")

    # タブ作成
    tab1, tab2 = st.tabs(["📅 月次給与振込", "📦 ストック振込"])

    # =====================================================
    # 月リスト生成（過去12か月）
    # =====================================================
    def generate_month_options():
        today = datetime.today()
        months = []
        for i in range(12):
            year = today.year
            month = today.month - i
            if month <= 0:
                month += 12
                year -= 1
            months.append(f"{year}-{month:02d}")
        return months

    month_options = generate_month_options()
    # =====================================================
    # ゆうちょ → 振込用形式へ変換
    # =====================================================
    def convert_yucho_to_bank_format(symbol, number):
        """
        symbol : ゆうちょ記号（5桁）
        number : ゆうちょ番号（8桁）
        → 支店コード(3桁)・口座番号(7桁)へ変換
        """
        symbol = "".join(filter(str.isdigit, str(symbol)))
        number = "".join(filter(str.isdigit, str(number)))

        branch_code = symbol[1:4]  # 2〜4桁目
        account_number = number[-7:].zfill(7)

        return branch_code, account_number

    # =====================================================
    # タブ1：月次給与振込（銀行振込担当者のみ）
    # =====================================================
    with tab1:
        selected_month = st.selectbox("対象年月", month_options)
        year, month = map(int, selected_month.split("-"))

        st.divider()

        salary_rows = SalaryConfirmRepository.get_confirmed_by_month(year, month)
        if not salary_rows:
            st.warning("この月の確定済み給与はありません")
        else:
            staff_list = StaffRepository.load_all()
            bank_staff_list = [s for s in staff_list if getattr(s, "payment_method", "bank") == "bank"]
            staff_map = {s.id: s for s in bank_staff_list}

            preview_rows = []
            total_transfer = 0

            for d in salary_rows:
                staff = staff_map.get(d["staff_id"])
                if not staff:
                    continue  # 銀行振込設定のない担当者はスキップ
                amount = d["total"]
                total_transfer += amount
                bank_code = getattr(staff, "bank_code", "")
                branch_code = getattr(staff, "branch_code", "")
                account_number = getattr(staff, "account_number", "")

                # --- ゆうちょ自動判定 ---
                if bank_code == "9900":
                    branch_code, account_number = convert_yucho_to_bank_format(
                        branch_code,
                        account_number
                    )
                else:
                    branch_code = str(branch_code).zfill(3)
                    account_number = str(account_number).zfill(7)

                preview_rows.append({
                    "氏名": staff.name,
                    "銀行コード": bank_code,
                    "支店コード": branch_code,
                    "口座種別": getattr(staff, "account_type", ""),
                    "口座番号": account_number,
                    "金額": amount
                })

            if not preview_rows:
                st.warning("銀行振込設定のある担当者はいません")
            else:
                df_preview = pd.DataFrame(preview_rows)
                st.dataframe(df_preview, use_container_width=True)
                st.metric("振込総額", f"¥{total_transfer:,}")

                if st.button("📤 月次振込CSV生成", use_container_width=True):
                    csv_data = df_preview.to_csv(index=False, encoding="cp932")
                    st.download_button(
                        label="📥 CSVダウンロード",
                        data=csv_data,
                        file_name=f"salary_transfer_{year}_{month}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

    # =====================================================
    # タブ2：ストック振込（銀行情報フォームあり・振込後に残高減算）
    # =====================================================
    with tab2:
        staff_list = StaffRepository.load_all()

        # stock_balance が None や文字列の場合は 0 に変換
        for s in staff_list:
            val = getattr(s, "stock_balance", 0)
            try:
                s.stock_balance = int(val)
            except:
                s.stock_balance = 0

        # ストックがある担当者だけ抽出
        stock_staff = [s for s in staff_list if s.payment_method == "stock"]

        if not stock_staff:
            st.info("現在ストックしている担当者はいません")
        else:
            staff_dict = {s.id: s for s in stock_staff}
            selected_id = st.selectbox(
                "担当者選択",
                options=list(staff_dict.keys()),
                format_func=lambda x: staff_dict[x].name
            )
            staff = staff_dict[selected_id]

            st.metric("現在ストック金額", f"¥{staff.stock_balance:,}")
            st.markdown("### 🏦 振込先銀行情報")

            bank_code = st.text_input(
                "銀行コード",
                value=getattr(staff, "bank_code", "")
            )

            branch_code = st.text_input(
                "支店コード",
                value=getattr(staff, "branch_code", "")
            )

            account_type = st.selectbox(
                "口座種別",
                ["普通", "当座"],
                index=0 if getattr(staff, "account_type", "普通") == "普通" else 1
            )

            account_number = st.text_input(
                "口座番号",
                value=getattr(staff, "account_number", "")
            )

            account_name = st.text_input(
                "口座名義",
                value=getattr(staff, "account_name", "")
            )

            # 振込金額入力
            pay_amount = st.number_input(
                "振込金額を入力",
                min_value=0,
                step=1000
            )

            if pay_amount > 0 and st.button("📤 ストック振込CSV生成", key=f"stock_csv_{staff.id}"):
                staff.bank_code = bank_code
                staff.branch_code = branch_code
                staff.account_type = account_type
                staff.account_number = account_number
                staff.account_name = account_name

                StaffRepository.save(staff)

                bank_code = staff.bank_code
                branch_code = staff.branch_code
                account_number = staff.account_number

                # --- ゆうちょ自動判定 ---
                if bank_code == "9900":
                    branch_code, account_number = convert_yucho_to_bank_format(
                        branch_code,
                        account_number
                    )
                else:
                    branch_code = str(branch_code).zfill(3)
                    account_number = str(account_number).zfill(7)

                preview = pd.DataFrame([{
                    "氏名": staff.name,
                    "銀行コード": bank_code,
                    "支店コード": branch_code,
                    "口座種別": staff.account_type,
                    "口座番号": account_number,
                    "金額": pay_amount
                }])
                st.dataframe(preview, use_container_width=True)

                # CSVダウンロード
                csv_data = preview.to_csv(index=False, encoding="cp932")
                st.download_button(
                    label="📥 CSVダウンロード",
                    data=csv_data,
                    file_name=f"stock_transfer_{staff.name}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

                # 振込後にストック残高を減算して保存
                staff.stock_balance -= pay_amount
                StaffRepository.save(staff)
                st.success(f"{staff.name} のストック残高を更新しました (残高: ¥{staff.stock_balance:,})")