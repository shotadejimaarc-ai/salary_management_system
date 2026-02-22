
def main():

    # pages/transfer_page.py

    import streamlit as st
    from datetime import datetime
    import pandas as pd

    from repositories.staff_repository import StaffRepository
    from repositories.salary_confirm_repository import SalaryConfirmRepository
    from ui.ui_style import apply_global_style

    apply_global_style()

    st.title("🏦 振込データ出力")

    tab1, tab2 = st.tabs(["📅 月次給与振込", "📦 ストック振込"])

    # =====================================================
    # ■ タブ① 月次給与振込
    # =====================================================
    with tab1:

        col1, col2 = st.columns(2)
        with col1:
            year = st.number_input("年", value=datetime.now().year)
        with col2:
            month = st.number_input("月", value=datetime.now().month)

        st.divider()

        salary_rows = SalaryConfirmRepository.get_confirmed_by_month(year, month)

        if not salary_rows:
            st.warning("この月の確定済み給与はありません")
            st.stop()

        staff_list = StaffRepository.load_all()
        staff_map = {s.id: s for s in staff_list}

        preview_rows = []
        total_transfer = 0

        for d in salary_rows:
            staff = staff_map.get(d["staff_id"])
            if not staff:
                continue

            amount = d["total"]
            total_transfer += amount

            preview_rows.append({
                "氏名": staff.name,
                "銀行コード": staff.bank_code,
                "支店コード": staff.branch_code,
                "口座種別": staff.account_type,
                "口座番号": staff.account_number,
                "金額": amount
            })

        df_preview = pd.DataFrame(preview_rows)

        st.dataframe(df_preview, use_container_width=True)
        st.metric("振込総額", f"¥{total_transfer:,}")

        if st.button("📤 月次振込CSV生成", use_container_width=True):

            csv_data = df_preview.to_csv(
                index=False,
                encoding="cp932"
            )

            st.download_button(
                label="📥 CSVダウンロード",
                data=csv_data,
                file_name=f"salary_transfer_{year}_{month}.csv",
                mime="text/csv",
                use_container_width=True
            )

    # =====================================================
    # ■ タブ② ストック振込
    # =====================================================
    with tab2:

        staff_list = StaffRepository.load_all()

        # ストックがある人だけ抽出
        stock_staff = [s for s in staff_list if getattr(s, "stock_amount", 0) > 0]

        if not stock_staff:
            st.info("現在ストックしている担当者はいません")
            st.stop()

        staff_dict = {s.id: s for s in stock_staff}

        selected_id = st.selectbox(
            "担当者選択",
            options=list(staff_dict.keys()),
            format_func=lambda x: staff_dict[x].name
        )

        staff = staff_dict[selected_id]

        st.metric("現在ストック金額", f"¥{staff.stock_amount:,}")

        pay_amount = st.number_input(
            "振込金額を入力",
            min_value=0,
            max_value=int(staff.stock_amount),
            step=1000
        )

        if pay_amount > 0:

            preview = pd.DataFrame([{
                "氏名": staff.name,
                "銀行コード": staff.bank_code,
                "支店コード": staff.branch_code,
                "口座種別": staff.account_type,
                "口座番号": staff.account_number,
                "金額": pay_amount
            }])

            st.dataframe(preview, use_container_width=True)

            if st.button("📤 ストック振込CSV生成", use_container_width=True):

                csv_data = preview.to_csv(
                    index=False,
                    encoding="cp932"
                )

                st.download_button(
                    label="📥 CSVダウンロード",
                    data=csv_data,
                    file_name=f"stock_transfer_{staff.name}.csv",
                    mime="text/csv",
                    use_container_width=True
                )