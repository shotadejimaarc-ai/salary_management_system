import streamlit as st
import pandas as pd
from repositories.salary_rule_repository import SalaryRuleRepository
from repositories.category_repository import CategoryRepository
from repositories.staff_repository import StaffRepository
from ui.ui_style import apply_global_style



def main():

    apply_global_style()

    st.title("💹 給与ルール管理")
    st.caption("POSと連動した給与計算ルールを管理します")

    data = SalaryRuleRepository.load()


    tab1, tab2, tab3 = st.tabs(["売上報酬F管理", "カテゴリ別F管理", "⚙ ストック残高調整"])

    # =====================================================
    # タブ1：売上報酬F管理（7段階対応）
    # =====================================================
    with tab1:

        st.subheader("組織売上Fに応じた報酬レート")

        rules = data.get("commission_rules", [])

        if not rules:
            rules = [
                {"min": 0, "max": 300000, "rate": 0.4},
                {"min": 300000, "max": 500000, "rate": 0.45},
                {"min": 500000, "max": None, "rate": 0.5},
            ]

        df = pd.DataFrame(rules)
        df.rename(columns={
            "min": "下限F",
            "max": "上限F",
            "rate": "報酬率(%)"
        }, inplace=True)

        df["報酬率(%)"] = df["報酬率(%)"] * 100

        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True
        )

        if st.button("売上報酬Fを保存", use_container_width=True):

            save_df = edited_df.copy()
            save_df["報酬率(%)"] = save_df["報酬率(%)"] / 100

            save_df.rename(columns={
                "下限F": "min",
                "上限F": "max",
                "報酬率(%)": "rate"
            }, inplace=True)

            data["commission_rules"] = save_df.to_dict("records")
            SalaryRuleRepository.save(data)

            st.success("保存完了")

    # =====================================================
    # タブ2：カテゴリ別F管理
    # =====================================================
    with tab2:
        st.divider()
        st.subheader("📥 カテゴリCSVインポート")

        uploaded_file = st.file_uploader(
            "カテゴリCSVを選択",
            type=["csv"]
        )

        if uploaded_file:

            df = pd.read_csv(uploaded_file)

            # 既存データを取得
            existing_master = CategoryRepository.load()

            updated_master = existing_master.copy()

            for _, row in df.iterrows():

                # 列名を自動判定（柔軟対応）
                if "category" in df.columns:
                    category_name = row["category"]
                elif "カテゴリ名" in df.columns:
                    category_name = row["カテゴリ名"]
                else:
                    st.error("カテゴリ名の列が見つかりません")
                    st.stop()

                # 既存データを残す安全設計
                old_data = existing_master.get(category_name, {})

                drink_back_flg = row.get("drink_back_flg", row.get("ドリンクバック", old_data.get("drink_back_flg", 0)))
                rate = row.get("rate", row.get("レート", old_data.get("rate", 0)))

                updated_master[category_name] = {
                    "drink_back_flg": int(drink_back_flg),
                    "rate": float(rate)
                }

            CategoryRepository.save(updated_master)

            st.success("カテゴリを安全にインポートしました（既存データ保持）")
            st.rerun()


        st.markdown("""
        <style>
        /* メインコンテンツ最大幅を制限 */
        .block-container {
            max-width: 700px;
            padding-left: 2rem;
            padding-right: 2rem;
        }
        </style>
        """, unsafe_allow_html=True)

        st.subheader("カテゴリ別Fレート設定")

        master = CategoryRepository.load()

        if not master:
            st.info("POSからカテゴリを同期してください")
            st.stop()

        updated = {}

        # ▼ 幅制限CSS
        st.markdown("""
            <style>
            .category-wrapper {
                max-width: 600px;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="category-wrapper">', unsafe_allow_html=True)

        # ヘッダー
        col1, col2 = st.columns([2, 1])
        col1.markdown("**カテゴリ名**")
        col2.markdown("**F率(%)**")

        st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)

        for category, config in master.items():

            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(
                    f"<div style='padding:6px 0;'>{category}</div>",
                    unsafe_allow_html=True
                )

            with col2:
                rate = st.number_input(
                    "",
                    value=int(config.get("rate", 0) * 100),
                    key=f"rate_{category}",
                    label_visibility="collapsed",
                    step=1,
                    min_value=0,
                    max_value=100
                )

            updated[category] = {
                "drink_back_flg": config.get("drink_back_flg", 0),
                "rate": rate / 100
            }

        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("カテゴリF率を保存"):
            CategoryRepository.save(updated)
            st.success("保存完了")
    
    # =====================================================
    # タブ3：ストック残高調整（途中導入対応）
    # =====================================================
    with tab3:

        st.subheader("⚙ ストック残高の手動設定")
        st.caption("途中導入用：現在のストック残高を直接入力して保存できます")

        staff_list = StaffRepository.load_all()

        if not staff_list:
            st.info("担当者データがありません")
            st.stop()

        # 数値変換の安全処理
        for s in staff_list:
            try:
                s.stock_balance = int(getattr(s, "stock_balance", 0))
            except:
                s.stock_balance = 0

        updated_values = {}

        st.divider()

        for staff in staff_list:

            col1, col2 = st.columns([2, 1])

            with col1:
                st.write(f"👤 {staff.name}")

            with col2:
                new_value = st.number_input(
                    "残高",
                    value=int(staff.stock_balance),
                    step=1000,
                    key=f"stock_adjust_{staff.id}"
                )

            updated_values[staff.id] = new_value

        st.divider()

        if st.button("💾 ストック残高を保存", type="primary", use_container_width=True):

            for staff in staff_list:
                staff.stock_balance = int(updated_values[staff.id])
                StaffRepository.save(staff)

            st.success("ストック残高を更新しました")
            st.rerun()