import streamlit as st
def main():

    import streamlit as st
    import pandas as pd
    from services.sales_sync_service import SalesSyncService
    from repositories.sales_repository import SalesRepository


    from ui.ui_style import apply_global_style
    apply_global_style()

    st.title("📲売上管理")
    tab1, tab2 = st.tabs(["売上CSV取込", "売上一覧"])


    # =============================
    # ① CSV取込タブ
    # =============================

    if st.session_state.get("reset_confirm_delete"):
        st.session_state["confirm_delete"] = False
        del st.session_state["reset_confirm_delete"]

    with tab1:

        uploaded_file = st.file_uploader("POS売上CSVアップロード", type="csv")

        import_mode = st.radio(
            "取込方法を選択",
            ["洗替取込", "追加取込"],
            horizontal=True
        )

        confirm_delete = False

        if import_mode == "洗替取込":
            st.warning("⚠ 洗替取込を選択しています。既存の売上データは全て削除されます。")
            confirm_delete = st.checkbox(
                "上記を理解した上で実行する",
                key="confirm_delete"
            )

        if uploaded_file:

            df = pd.read_csv(uploaded_file)

            st.subheader("プレビュー")
            st.dataframe(df.head(20), use_container_width=True)
            st.write(f"件数: {len(df)}件")

            button_disabled = (
                import_mode == "洗替取込" and not confirm_delete
            )

            if st.button("取込実行", disabled=button_disabled):

                if import_mode == "洗替取込":
                    SalesRepository.delete_all()

                SalesSyncService.sync_from_df(df)

                st.session_state["reset_confirm_delete"] = True
                st.session_state["import_done"] = len(df)
                st.rerun()

        if st.session_state.get("import_done"):
            st.success(f"{st.session_state['import_done']}件 取込完了")
            del st.session_state["import_done"]


    # =============================
    # ② 売上一覧タブ
    # =============================
    with tab2:

        sales = SalesRepository.load_all()

        if not sales:
            st.info("売上データなし")
        else:
            table_data = []

            for s in sales:
                table_data.append({
                    "営業日": s.sales_date,
                    "担当ID": s.staff_id,
                    "担当者名": s.staff_name,
                    "カテゴリ": s.category,
                    "商品名": s.product_name,
                    "金額": f"{int(s.amount):,} 円"
                })

            # 営業日降順
            table_data.sort(key=lambda x: x["営業日"], reverse=True)

            st.dataframe(table_data, use_container_width=True)

            total_amount = sum(s.amount for s in sales)
            st.metric("総売上", f"{total_amount:,} 円")
