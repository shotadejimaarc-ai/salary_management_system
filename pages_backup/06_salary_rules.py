import streamlit as st
from repositories.salary_rule_repository import SalaryRuleRepository
from repositories.category_repository import CategoryRepository
import pandas as pd

from ui.ui_style import apply_global_style
apply_global_style()

st.markdown('<div class="sticky-header">', unsafe_allow_html=True)
st.title("💹給与ルール管理")
st.markdown('</div>', unsafe_allow_html=True)

data = SalaryRuleRepository.load()

tab1, tab2 = st.tabs(["売上報酬F管理", "ドリンクバック管理"])

# ===================================
# タブ1：歩合管理
# ===================================
with tab1:

    st.subheader("全体売上に応じた歩合率")

    rules = data.get("commission_rules", [])
    new_rules = []

    for i, rule in enumerate(rules):

        col1, col2, col3 = st.columns([2,2,1])

        min_val = col1.number_input(
            "売上下限",
            value=rule["min"],
            key=f"min_{i}"
        )

        max_val = col2.number_input(
            "売上上限 (未設定なら0)",
            value=rule["max"] if rule["max"] else 0,
            key=f"max_{i}"
        )

        rate = col3.number_input(
            "率 (%)",
            value=int(rule["rate"] * 100),
            key=f"rate_{i}"
        )

        new_rules.append({
            "min": min_val,
            "max": max_val if max_val != 0 else None,
            "rate": rate / 100
        })

    if st.button("売上報酬Fを保存"):
        data["commission_rules"] = new_rules
        SalaryRuleRepository.save(data)
        st.success("保存完了")


# ===================================
# タブ2：ドリンクバック管理
# ===================================
with tab2:

    st.subheader("POSカテゴリCSV取込")

    uploaded_cat_file = st.file_uploader("カテゴリCSVアップロード", type="csv")

    # ===============================
    # CSV取込処理（マスタ更新）
    # ===============================
    if uploaded_cat_file:

        df = pd.read_csv(uploaded_cat_file)
        df.columns = df.columns.str.strip()

        master = CategoryRepository.load()

        for _, row in df.iterrows():

            category_name = row["カテゴリ名"]
            drink_back_flg = int(row["売上バックFLG"])

            existing_rate = master.get(category_name, {}).get("rate", 0)

            master[category_name] = {
                "drink_back_flg": drink_back_flg,
                "rate": existing_rate
            }

        CategoryRepository.save(master)
        st.success("カテゴリ同期完了")

    # ===============================
    # 常にマスタから表示
    # ===============================
    st.subheader("ドリンクバック率管理")

    master = CategoryRepository.load()

    if not master:
        st.info("カテゴリがまだ登録されていません")
        st.stop()

    updated = {}

    # 中央寄せ
    space_left, main_col, space_right = st.columns([1, 2, 1])

    with main_col:

        st.markdown(
            '<div class="category-header">カテゴリ　｜　バック率(%)</div>',
            unsafe_allow_html=True
        )

        for category, config in master.items():

            col1, col2 = st.columns([3, 1])

            if config["drink_back_flg"] == 1:

                with col1:
                    st.markdown(
                        f'<div class="category-row">{category}</div>',
                        unsafe_allow_html=True
                    )

                with col2:
                    rate = st.number_input(
                        "",
                        value=int(config.get("rate", 0) * 100),
                        key=f"rate_{category}",
                        label_visibility="collapsed"
                    )

                updated[category] = {
                    "drink_back_flg": 1,
                    "rate": rate / 100
                }

            else:
                with col1:
                    st.markdown(
                        f'<div class="category-row" style="color:#777;">{category}</div>',
                        unsafe_allow_html=True
                    )

                with col2:
                    st.markdown(
                        '<div class="category-row" style="color:#777;">対象外</div>',
                        unsafe_allow_html=True
                    )

                updated[category] = config

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("ドリンクバック率保存"):
            CategoryRepository.save(updated)
            st.success("保存完了")
