import streamlit as st
from services.sales_distribution_service import SalesDistributionService
from repositories.staff_repository import StaffRepository
from repositories.sales_repository import SalesRepository

from ui.ui_style import apply_global_style
apply_global_style()

# =============================
# データ取得
# =============================
result = SalesDistributionService.calculate()

personal = result["personal_sales"]
total = result["total_sales"]
overall = result["overall_sales"]
drink_back_categories = result.get("drink_back_categories", [])

staff_list = StaffRepository.load_all()

if not staff_list:
    st.warning("⚠ 管理者マスタが未登録です。先にスタッフ登録を行ってください。")
    st.stop()

staff_dict = {staff.id: staff for staff in staff_list}

# =============================
# ヘッダー
# =============================
st.markdown('<div class="sticky-header">', unsafe_allow_html=True)
st.title("💽売上分析")

selected_id = st.selectbox(
    "担当者を選択",
    options=[staff.id for staff in staff_list],
    format_func=lambda x: staff_dict[x].name
)

selected_staff = staff_dict[selected_id]

col1, col2 = st.columns(2)

with col1:
    st.metric("個人売上", f"{int(personal.get(selected_id, 0)):,} 円")

with col2:
    st.metric("組織売上", f"{int(total.get(selected_id, 0)):,} 円")

st.markdown('</div>', unsafe_allow_html=True)

# =============================
# 売上明細（ドリンクバック除外しない）
# =============================
st.subheader("売上明細")

all_sales = SalesRepository.find_by_staff(selected_id)

sales = all_sales

if not sales:
    st.write("明細なし")
else:
    st.dataframe([
        {
            "営業日": s.sales_date,
            "担当者名": s.staff_name,
            "カテゴリ": s.category,
            "商品名": s.product_name,
            "金額": f"{int(s.amount):,} 円"
        } for s in sales
    ], use_container_width=True)


# =============================
# 子メンバー内訳
# =============================
st.subheader("子メンバー内訳")

children = [s for s in staff_list if selected_id in (s.parents or [])]

if not children:
    st.info("子メンバーなし")
else:
    for child in children:
        with st.container(border=True):

            st.markdown(f"### 👤 {child.name}")

            c1, c2 = st.columns(2)

            with c1:
                st.metric("個人売上", f"{int(personal.get(child.id, 0)):,} 円")

            with c2:
                st.metric("組織売上", f"{int(total.get(child.id, 0)):,} 円")

            all_child_sales = SalesRepository.find_by_staff(child.id)

            child_sales = [
                s for s in all_child_sales
                if s.category not in drink_back_categories
            ]

            if child_sales:
                st.dataframe([
                    {
                        "営業日": s.sales_date,
                        "担当者名": s.staff_name,
                        "カテゴリ": s.category,
                        "商品名": s.product_name,
                        "金額": f"{int(s.amount):,} 円"
                    } for s in child_sales
                ], use_container_width=True)
