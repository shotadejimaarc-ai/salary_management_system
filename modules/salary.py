# salary.py
import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from repositories.staff_repository import StaffRepository
from repositories.category_repository import CategoryRepository
from repositories.salary_rule_repository import SalaryRuleRepository
from services.salary_service import SalaryService
from services.sales_service import SalesService
from repositories.sales_repository import SalesRepository
from repositories.salary_confirm_repository import SalaryConfirmRepository
from ui.ui_style import apply_global_style

# PDF用
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics

def main():
    apply_global_style()

    st.markdown("""
    <style>
    .block-container { padding-top: 2.2rem; padding-left: 1rem; padding-right: 1rem; }
    html, body, [class*="css"] { background-color: #111317 !important; color: #f2f2f2 !important; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Hiragino Kaku Gothic ProN", "Inter", sans-serif; }
    h1 { font-weight:600; font-size:20px; letter-spacing:0.2px; margin-bottom:1.4rem; }

    .total-label { font-size:12px; color:#8b949e; letter-spacing:0.6px; }
    .total-value { font-size:50px; font-weight:600; margin-top:4px; letter-spacing:-0.5px; }
    .total-value span { font-size:18px; margin-right:4px; opacity:0.6; }

    .section-title { font-size:13px; font-weight:600; margin-bottom:8px; margin-top:24px; color:#9aa4b2; }

    div[data-testid="stMetric"] { background:#1c1f26; padding:14px; border-radius:14px; border:1px solid #2a2f38; margin-bottom:10px; transition:0.15s ease; }
    div[data-testid="stMetric"] label { font-size:11px !important; color:#9aa4b2 !important; }
    div[data-testid="stMetric"] div { font-size:16px !important; }
    div[data-testid="stMetric"]:hover { transform:translateY(-2px); border:1px solid #3a3f4a; }

    .stButton > button { background:#1c1f26; border:1px solid #2a2f38; border-radius:12px; height:42px; font-weight:600; font-size:13px; }
    .stButton > button:hover { background:#232733; }

    .status-row { background: linear-gradient(145deg, #1c1f26, #181b21); padding:18px 18px; border-radius:18px; border:1px solid #2a2f38; margin-bottom:14px; min-height:70px; display:flex; align-items:center; transition:all 0.2s ease; }
    .status-row:hover { border:1px solid #3b4252; box-shadow:0 4px 18px rgba(0,0,0,0.4); transform:translateY(-3px); }
    .status-amount { font-weight:600; font-size:18px; letter-spacing:0.3px; }
    .status-confirmed { color:#34d399; font-weight:600; letter-spacing:0.3px; }
    .status-unconfirmed { color:#f87171; font-weight:600; letter-spacing:0.3px; }

    .status-row-confirmed { background:linear-gradient(145deg, rgba(34, 197, 94, 0.08), rgba(16, 185, 129, 0.05)); border:1px solid rgba(52, 211, 153, 0.25); }
    .status-row-confirmed:hover { box-shadow:0 4px 22px rgba(34, 197, 94, 0.15); }

    div[data-testid="column"] .stDownloadButton > button { height:40px; border-radius:12px; font-weight:600; font-size:13px; }
    </style>
    """, unsafe_allow_html=True)

    st.title("💰給与管理")
    tab1, tab2, tab3 = st.tabs(["バイト情報入力", "給与確認", "状態確認"])

    # =====================================================
    # データロード
    # =====================================================
    staff_list = StaffRepository.load_all()
    category_master = CategoryRepository.load()
    salary_rules = SalaryRuleRepository.load()

    if not staff_list:
        st.warning("担当者が登録されていません")
        st.stop()

    # =====================================================
    # 月生成関数
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

    # =====================================================
    # タブ1：バイト情報入力
    # =====================================================
    with tab1:
        st.markdown("### 🧑‍🧒 バイト情報一括入力")

        # バイトのみ取得
        part_time_staff = [s for s in staff_list if s.type == "baito"]

        if not part_time_staff:
            st.info("現在登録されているバイト担当者はいません")
        else:
            # データをリストで保持して編集
            for staff in part_time_staff:
                st.markdown(f"#### {staff.name}")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    staff.hourly_wage = st.number_input(
                        "時給",
                        min_value=0,
                        value=getattr(staff, "hourly_wage", 0),
                        key=f"hourly_{staff.id}"
                    )
                with col2:
                    staff.working_hours = st.number_input(
                        "稼働時間",
                        min_value=0.0,
                        value=getattr(staff, "working_hours", 0.0),
                        key=f"hours_{staff.id}"
                    )
                with col3:
                    staff.work_days = st.number_input(
                        "出勤日数",
                        min_value=0,
                        value=getattr(staff, "work_days", 0),
                        key=f"days_{staff.id}"
                    )
                with col4:
                    staff.transportation_cost = st.number_input(
                        "交通費（片道）",
                        min_value=0,
                        value=getattr(staff, "transportation_cost", 0),
                        key=f"transport_{staff.id}"
                    )

                base_salary = staff.hourly_wage * staff.working_hours
                transport_total = staff.transportation_cost * staff.work_days * 2
                st.write(f"給与試算: 時給分 ¥{int(base_salary):,} + 交通費 ¥{int(transport_total):,} = 合計 ¥{int(base_salary+transport_total):,}")

            if st.button("💾 一括保存"):
                for staff in part_time_staff:
                    StaffRepository.save(staff)
                st.success("すべてのバイト情報を保存しました ✅")

    # =============================
    # タブ2：給与確認（完成版）
    # =============================
    with tab2:
        # 担当者選択＆年月選択 横並び
        col1, col2 = st.columns([0.6, 0.4])
        with col1:
            selected_name = st.selectbox("", [s.name for s in staff_list])
        with col2:
            selected_month_str = st.selectbox("", generate_month_options())

        year, month = map(int, selected_month_str.split("-"))
        staff = next(s for s in staff_list if s.name == selected_name)

        # 売上取得
        own_sales = SalesRepository.find_by_staff_and_month(staff.id, selected_month_str)
        summary = SalesService.get_monthly_sales_summary_by_staff(
            staff_id=staff.id,
            target_month=selected_month_str
        )

        # =============================
        # 給与計算
        # =============================
        if staff.type == "staff":
            # スタッフ給与
            result = SalaryService.calculate_staff_salary(
                staff,
                summary,
                salary_rules.get("commission_rules", []),
                category_master
            )
            total_amount = result["total"]
            commission_rate = result.get("commission_rate", 0)
        else:
            # バイト給与
            hourly_wage = getattr(staff, "hourly_wage", 0)
            working_hours = getattr(staff, "working_hours", 0)
            work_days = getattr(staff, "work_days", 0)
            transportation_cost = getattr(staff, "transportation_cost", 0)
            base_salary = hourly_wage * working_hours
            transport_total = transportation_cost * work_days * 2

            # ドリンクバック合計
            f_categories = [c for c in category_master if category_master[c].get("drink_back_flg",0)==1]
            drink_back_total = 0
            for sale in own_sales:
                if sale.category in f_categories:
                    rate = category_master[sale.category].get("rate",0)
                    drink_back_total += int(sale.amount * rate)

            total_amount = int(base_salary + transport_total + drink_back_total)
            result = {
                "base_salary": base_salary,
                "transport_total": transport_total,
                "drink_back_total": drink_back_total,
                "total": total_amount
            }
            commission_rate = "-"  # バイトは総支給額のレート表示なし

        # =============================
        # 総支給額表示（給与内訳の上）
        # =============================
        st.markdown(f"""
        <div class="total-wrapper">
            <div class="total-main-label">総支給額</div>
            <div class="total-value">¥{int(round(total_amount)):,}</div>
            <div class="total-meta"> F: {int(summary.get('personal_sales_f',0)) if staff.type=='staff' else '-'} / Rate: {commission_rate} </div>
        </div>
        """, unsafe_allow_html=True)

        # =============================
        # 給与内訳（スタッフ／バイト共通ボタン風横並び）
        # =============================
        st.markdown('<div class="section-title">給与内訳</div>', unsafe_allow_html=True)
        c1, c2, c3, c4, c5, c6 = st.columns(6)

        if staff.type == "staff":
            c1.metric("個人売上金額", f"¥{int(summary.get('personal_sales_amount',0)):,}")
            c2.metric("個人売上F", f"{int(summary.get('personal_sales_f',0)):,}")
            c3.metric("組織売上金額", f"¥{int(summary.get('org_sales_amount',0)):,}")
            c4.metric("組織売上F", f"{int(summary.get('org_sales_f',0)):,}")
            c5.metric("適用レート", f"{commission_rate*100:.1f}%")
            c6.metric("家賃", "¥2,000")
        else:
            c1.metric("時給", f"¥{hourly_wage}")
            c2.metric("稼働時間", f"{working_hours}")
            c3.metric("出勤日数", f"{work_days}")
            c4.metric("交通費", f"¥{transport_total}")
            c5.metric("ドリンクバック合計", f"¥{drink_back_total}")
            c6.metric("総支給額", f"¥{total_amount}")

        # =============================
        # 組織売上明細
        # =============================
        st.markdown('<div class="section-title">組織売上明細</div>', unsafe_allow_html=True)
        detail_rows = []

        # 本人売上
        for sale in own_sales:
            detail_rows.append({
                "営業日": sale.sales_date,
                "担当者名": sale.staff_name,
                "カテゴリ": sale.category,
                "商品名": sale.product_name,
                "売上": sale.amount,
                "親分配率": "-",
                "計上額": sale.amount
            })

        # 子担当者売上
        children = [s for s in staff_list if s.parents and staff.id in s.parents]
        for child in children:
            child_sales = SalesRepository.find_by_staff_and_month(child.id, selected_month_str)
            parent_count = len(child.parents)
            allocation_rate = 1.0 if parent_count == 1 else 0.5
            for sale in child_sales:
                detail_rows.append({
                    "営業日": sale.sales_date,
                    "担当者名": sale.staff_name,
                    "カテゴリ": sale.category,
                    "商品名": sale.product_name,
                    "売上": sale.amount,
                    "親分配率": f"{int(allocation_rate*100)}%",
                    "計上額": int(sale.amount * allocation_rate)
                })

        if detail_rows:
            detail_rows.sort(key=lambda x: x["営業日"], reverse=True)
            st.dataframe(detail_rows, use_container_width=True)
        else:
            st.info("該当する売上明細なし")

        # 給与確定ボタンと出力
        confirm_data = SalaryConfirmRepository.find(staff.id, year, month)
        col1,col2 = st.columns([2,2])
        with col1:
            if confirm_data:
                st.success(f"✅ 確定済（総額 ¥{confirm_data['total']:,}）")
            else:
                st.info("未確定")
        with col2:
            if st.button("給与確定", key=f"confirm_{staff.id}_{year}_{month}", disabled=bool(confirm_data)):
                total_amount = int(result.get("total",0))
                if staff.type=="baito":
                    total_amount += drink_back_total
                if staff.payment_method=="stock":
                    staff.stock_balance += total_amount
                    StaffRepository.save(staff)
                SalaryConfirmRepository.confirm(staff.id, year, month, total_amount)
                st.success("給与確定しました")
                st.rerun()
            if confirm_data:
                # 確定後はExcel/PDF出力
                df_export = pd.DataFrame([{"担当者":staff.name,"対象月":selected_month_str,"総支給額":total_amount}])
                excel_buffer = BytesIO()
                df_export.to_excel(excel_buffer,index=False)
                pdf_buffer = BytesIO()
                doc = SimpleDocTemplate(pdf_buffer,pagesize=A4)
                pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
                doc.build([])
                b1,b2 = st.columns(2)
                with b1:
                    st.download_button("Excel出力", excel_buffer.getvalue(), file_name=f"{staff.name}_{selected_month_str}_salary.xlsx")
                with b2:
                    st.download_button("PDF出力", pdf_buffer.getvalue(), file_name=f"{staff.name}_{selected_month_str}_salary.pdf")

    # =====================================================
    # タブ3：状態確認（HTMLなし安定版）
    # =====================================================
    with tab3:

        st.markdown("## 📊 給与確定状況")

        selected_month_status = st.selectbox(
            "対象月",
            generate_month_options(),
            key="status_month"
        )

        year_status, month_status = map(int, selected_month_status.split("-"))

        st.divider()

        cols = st.columns(3)

        index = 0

        for staff in staff_list:

            with cols[index % 3]:

                summary = SalesService.get_monthly_sales_summary_by_staff(
                    staff.id,
                    selected_month_status
                )

                # ===== 給与計算 =====
                if staff.type == "staff":
                    result = SalaryService.calculate_staff_salary(
                        staff,
                        summary,
                        salary_rules.get("commission_rules", []),
                        category_master
                    )
                    total = result["total"]
                else:
                    result = SalaryService.calculate_part_time_salary(
                        staff,
                        summary,
                        category_master
                    )

                    f_categories = {
                        k: v for k, v in category_master.items()
                        if v.get("drink_back_flg", 0) == 1
                    }

                    drink_back_total = 0
                    own_sales = SalesRepository.find_by_staff_and_month(
                        staff.id,
                        selected_month_status
                    )

                    for sale in own_sales:
                        if sale.category in f_categories:
                            drink_back_total += int(
                                sale.amount * f_categories[sale.category]["rate"]
                            )

                    total = result["total"] + drink_back_total

                confirm = SalaryConfirmRepository.find(
                    staff.id,
                    year_status,
                    month_status
                )

                # ===== 表示整形 =====
                total_display = f"¥{int(round(total)):,}" if total else "-"

                if confirm:
                    st.success(f"{staff.name}")
                    st.metric("支給額", total_display)
                    st.caption("✅ 確定済")
                else:
                    st.warning(f"{staff.name}")
                    st.metric("支給額", total_display)
                    st.caption("⚠ 未確定")

            index += 1
            
if __name__=="__main__":
    main()