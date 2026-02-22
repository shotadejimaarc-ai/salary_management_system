import streamlit as st
from services.sales_distribution_service import SalesDistributionService
from repositories.staff_repository import StaffRepository
from repositories.sales_repository import SalesRepository
from ui.ui_style import apply_global_style


def main():

    apply_global_style()

    # =============================
    # データ取得
    # =============================
    distribution = SalesDistributionService.calculate()
    staff_list = StaffRepository.load_all()

    if not staff_list:
        st.warning("⚠ 管理者マスタが未登録です。先にスタッフ登録を行ってください。")
        st.stop()

    staff_dict = {staff.id: staff for staff in staff_list}

    # =============================
    # ヘッダー
    # =============================
    st.markdown('<div class="sticky-header">', unsafe_allow_html=True)

    st.title("💽 売上分析")

    selected_id = st.selectbox(
        "担当者を選択",
        options=[staff.id for staff in staff_list],
        format_func=lambda x: staff_dict[x].name
    )

    selected_staff = staff_dict[selected_id]
    data = distribution.get(selected_id, {})

    personal_amount = data.get("personal_sales_amount", 0)
    children_amount = data.get("children_sales_amount", 0)
    org_amount = personal_amount + children_amount

    personal_f = data.get("personal_sales_f", 0)
    children_f = data.get("children_sales_f", 0)
    org_f = data.get("org_sales_f", 0)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("個人売上", f"{int(personal_amount):,} 円")

    with col2:
        st.metric("組織売上", f"{int(org_amount):,} 円")

    with col3:
        st.metric("組織F", f"{int(org_f):,}")

    st.markdown('</div>', unsafe_allow_html=True)


    # =============================
    # 売上明細
    # =============================
    st.subheader("売上明細")

    sales = SalesRepository.find_by_staff(selected_id)

    if not sales:
        st.write("明細なし")
    else:
        st.dataframe(
            [
                {
                    "営業日": s.sales_date,
                    "担当者名": s.staff_name,
                    "カテゴリ": s.category,
                    "商品名": s.product_name,
                    "金額": f"{int(s.amount):,} 円"
                }
                for s in sales
            ],
            use_container_width=True
        )

    # =============================
    # 子メンバー内訳
    # =============================
    st.subheader("子メンバー内訳")

    children = [s for s in staff_list if selected_id in (s.parents or [])]

    if not children:
        st.info("子メンバーなし")
    else:
        for child in children:

            child_data = distribution.get(child.id, {})

            child_personal = child_data.get("personal_sales_amount", 0)
            child_children = child_data.get("children_sales_amount", 0)
            child_org = child_personal + child_children
            child_f = child_data.get("org_sales_f", 0)

            with st.container(border=True):

                st.markdown(f"### 👤 {child.name}")

                c1, c2, c3 = st.columns(3)

                with c1:
                    st.metric("個人売上", f"{int(child_personal):,} 円")

                with c2:
                    st.metric("組織売上", f"{int(child_org):,} 円")

                with c3:
                    st.metric("組織F", f"{int(child_f):,}")

                child_sales = SalesRepository.find_by_staff(child.id)

                if child_sales:
                    st.dataframe(
                        [
                            {
                                "営業日": s.sales_date,
                                "カテゴリ": s.category,
                                "商品名": s.product_name,
                                "金額": f"{int(s.amount):,} 円"
                            }
                            for s in child_sales
                        ],
                        use_container_width=True
                    )