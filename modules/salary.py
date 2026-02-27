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
    /* ========================= */
    /* バイト入力カード（整理版） */
    /* ========================= */

    .part-card {
        background: linear-gradient(145deg, #1c1f26, #181b21);
        border: 1px solid #2a2f38;
        border-radius: 18px;
        padding: 20px;
        margin: 0 0 18px 0;   /* ← 上余白完全排除 */
        transition: all 0.2s ease;
    }

    .part-card:hover {
        border: 1px solid #3b4252;
        box-shadow: 0 6px 24px rgba(0,0,0,0.4);
        transform: translateY(-3px);
    }

    /* Streamlitブロック余白対策（安定版） */
    div[data-testid="stVerticalBlock"] > div {
        margin-top: 0px !important;
    }

    /* ========================= */
    /* 担当者名（見やすく） */
    /* ========================= */

    .part-name {
        font-size: 20px;
        font-weight: 700;
        letter-spacing: 0.4px;
        margin-bottom: 12px;
        color: #f8fafc;
    }

    /* ========================= */
    /* コンパクト入力 */
    /* ========================= */

    div[data-testid="stNumberInput"] input {
        height: 36px !important;
        font-size: 13px !important;
        padding: 6px 10px !important;
    }

    div[data-testid="stNumberInput"] label {
        font-size: 11px !important;
        color: #8b949e !important;
    }

    /* ========================= */
    /* 合計金額 */
    /* ========================= */

    .total-amount {
        text-align: left;      /* ← 右寄せやめた */
        font-weight: 700;
        font-size: 20px;
        color: #34d399;
        margin-top: 12px;
        transition: all 0.25s ease;
    }

    .total-amount.animate {
        transform: scale(1.08);
        text-shadow: 0 0 12px rgba(52,211,153,0.6);
    }

    /* ========================= */
    /* 編集ハイライト */
    /* ========================= */

    .part-card.edited {
        border: 1px solid #fbbf24;
        background: linear-gradient(
            145deg,
            rgba(251,191,36,0.08),
            rgba(251,191,36,0.04)
        );
    }

    /* ========================= */
    /* 固定保存バー */
    /* ========================= */

    .fixed-save-bar {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #111317;
        border-top: 1px solid #2a2f38;
        padding: 14px 24px;
        z-index: 999;
        display: flex;
        justify-content: flex-end;
    }

    .fixed-save-bar button {
        height: 42px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 14px;
    }
    /* ===================================== */
    /* タブ直下の謎の余白（帯）の完全除去 */
    /* ===================================== */

    /* タブ内コンテナ上部の余白削除 */
    section.main > div {
        padding-top: 0rem !important;
    }

    /* block-containerの上余白を完全ゼロに */
    .block-container {
        padding-top: 1rem !important;
    }

    /* タブパネルの上余白を潰す */
    div[role="tabpanel"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }

    /* 最初の要素のマージン潰し */
    div[role="tabpanel"] > div:first-child {
        margin-top: 0 !important;
    }
    
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
    # タブ1：バイト情報入力
    with tab1:
        st.markdown(
            '<div style="margin-top:0; margin-bottom:6px; font-size:18px; font-weight:600;">🧑‍🧒 バイト情報一括入力</div>',
            unsafe_allow_html=True
        )

        part_time_staff = [s for s in staff_list if s.type == "baito"]

        if not part_time_staff:
            st.info("現在登録されているバイト担当者はいません")
        else:
            for staff in part_time_staff:

                if f"original_{staff.id}" not in st.session_state:
                    st.session_state[f"original_{staff.id}"] = {
                        "hourly": getattr(staff, "hourly_wage", 0),
                        "hours": getattr(staff, "working_hours", 0),
                        "days": getattr(staff, "work_days", 0),
                        "transport": getattr(staff, "transportation_cost", 0),
                        "last_total": 0
                    }

                original = st.session_state[f"original_{staff.id}"]

                # ===== カード開始 =====
                st.markdown('<div class="part-card">', unsafe_allow_html=True)

                # 👤 担当者名（カード最上部・余白ゼロ）
                st.markdown(
                    f'<div class="part-name" style="margin-top:0; margin-bottom:8px;">{staff.name}</div>',
                    unsafe_allow_html=True
                )

                # 入力欄（横並び）
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    staff.hourly_wage = st.number_input(
                        "時給", min_value=0, value=original["hourly"], key=f"hourly_{staff.id}"
                    )
                with col2:
                    staff.working_hours = st.number_input(
                        "稼働時間", min_value=0.0, value=original["hours"], key=f"hours_{staff.id}"
                    )
                with col3:
                    staff.work_days = st.number_input(
                        "出勤日数", min_value=0, value=original["days"], key=f"days_{staff.id}"
                    )
                with col4:
                    staff.transportation_cost = st.number_input(
                        "交通費（片道）", min_value=0, value=original["transport"], key=f"transport_{staff.id}"
                    )

                # 合計計算
                base_salary = staff.hourly_wage * staff.working_hours
                transport_total = staff.transportation_cost * staff.work_days * 2
                total = base_salary + transport_total

                animate_class = ""
                if total != original["last_total"]:
                    animate_class = "animate"
                    st.session_state[f"original_{staff.id}"]["last_total"] = total

                # 💰 合計表示（左寄せ・アニメ維持）
                st.markdown(
                    f'<div class="total-amount {animate_class}">合計 ¥{int(total):,}</div>',
                    unsafe_allow_html=True
                )

                # カード終了
                st.markdown('</div>', unsafe_allow_html=True)


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
            result = SalaryService.calculate_staff_salary(
                staff,
                summary,
                salary_rules.get("commission_rules", []),
                category_master
            )
            total_amount = result["total"]
            commission_rate = f"{result.get('commission_rate', 0)*100:.1f}%"
        else:
            # バイト給与
            hourly_wage = getattr(staff, "hourly_wage", 0)
            working_hours = getattr(staff, "working_hours", 0)
            work_days = getattr(staff, "work_days", 0)
            transportation_cost = getattr(staff, "transportation_cost", 0)
            base_salary = hourly_wage * working_hours
            transport_total = transportation_cost * work_days * 2

            f_categories = [c for c in category_master if category_master[c].get("drink_back_flg",0)==1]
            drink_back_total = 0
            for sale in own_sales:
                if sale.category in f_categories:
                    rate = category_master[sale.category].get("rate",0)
                    drink_back_total += int(sale.amount * rate)

            total_amount = int(base_salary + transport_total + drink_back_total)
            result = {
                "type": "part_time",
                "total": total_amount,
                "base_salary": base_salary,
                "transportation": transport_total,
                "drink_back_total": drink_back_total
            }
            commission_rate = "-"

        # =============================
        # 総支給額表示
        # =============================
        st.markdown(f"""
        <div class="total-wrapper">
            <div class="total-main-label">総支給額</div>
            <div class="total-value">¥{int(round(total_amount)):,}</div>
            <div class="total-meta"> F: {int(summary.get('personal_sales_f',0)) if staff.type=='staff' else '-'} / Rate: {commission_rate} </div>
        </div>
        """, unsafe_allow_html=True)

        # =============================
        # 給与内訳
        # =============================
        st.markdown('<div class="section-title">給与内訳</div>', unsafe_allow_html=True)
        cols = st.columns(6)
        if staff.type == "staff":
            cols[0].metric("個人売上金額", f"¥{int(summary.get('personal_sales_amount',0)):,}")
            cols[1].metric("個人売上F", f"{int(summary.get('personal_sales_f',0)):,}")
            cols[2].metric("組織売上金額", f"¥{int(summary.get('org_sales_amount',0)):,}")
            cols[3].metric("組織売上F", f"{int(summary.get('org_sales_f',0)):,}")
            cols[4].metric("適用レート", commission_rate)
            cols[5].metric("家賃", "¥2,000")
        else:
            cols[0].metric("時給", f"¥{hourly_wage}")
            cols[1].metric("稼働時間", f"{working_hours}")
            cols[2].metric("出勤日数", f"{work_days}")
            cols[3].metric("交通費", f"¥{transport_total}")
            cols[4].metric("ドリンクバック合計", f"¥{drink_back_total}")
            cols[5].metric("総支給額", f"¥{total_amount}")

        # =============================
        # 組織売上明細
        # =============================
        st.markdown('<div class="section-title">組織売上明細</div>', unsafe_allow_html=True)
        detail_rows = []

        for sale in own_sales:
            detail_rows.append({
                "営業日": sale.sales_date,
                "担当者名": sale.staff_name,
                "カテゴリ": sale.category,
                "商品名": sale.product_name,
                "売上": int(sale.amount),
                "親分配率": "-",
                "計上額": int(sale.amount)
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
                    "売上": int(sale.amount),
                    "親分配率": f"{int(allocation_rate*100)}%",
                    "計上額": int(sale.amount * allocation_rate)
                })

        if detail_rows:
            detail_rows.sort(key=lambda x: x["営業日"], reverse=True)
            st.dataframe(detail_rows, use_container_width=True)
        else:
            st.info("該当する売上明細なし")

        # =============================
        # 給与確定＆Excel/PDF出力
        # =============================
        confirm_data = SalaryConfirmRepository.find(staff.id, year, month)
        col1, col2 = st.columns([2,2])
        with col1:
            if confirm_data:
                st.success(f"✅ 確定済（総額 ¥{confirm_data['total']:,}）")
            else:
                st.info("未確定")
        with col2:
            if st.button("給与確定", key=f"confirm_{staff.id}_{year}_{month}", disabled=bool(confirm_data)):
                total_amount = int(result.get("総支給額",0))
                if staff.type=="baito":
                    total_amount += result.get("ドリンクバック合計",0)
                if staff.payment_method=="stock":
                    staff.stock_balance += total_amount
                    StaffRepository.save(staff)
                SalaryConfirmRepository.confirm(staff.id, year, month, total_amount)
                st.success("給与確定しました")
                st.rerun()
            
            

            if confirm_data:
                # Excel/PDF出力
                
                from modules.salary_export import generate_salary_excel_pdf_full

                
                # ===== export用データ統合 =====
                safe_result = result.copy()
                # for k, v in result.items():
                #     try:
                #         safe_result[k] = int(v)
                #     except (ValueError, TypeError):
                #         safe_result[k] = str(v)
                from modules.salary_export import generate_salary_excel_pdf_full

                safe_result = result.copy()

                # ① 先にDataFrame化
                import pandas as pd
                detail_df = pd.DataFrame(detail_rows)

                # ② 列名変換
                detail_df = detail_df.rename(columns={
                    "営業日": "date",
                    "担当者名": "staff_name",
                    "カテゴリ": "category",
                    "商品名": "product_name",
                    "売上": "sales_amount",
                    "親分配率": "rate",
                    "計上額": "calculated_amount"
                })
            
                # ③ 変換後を渡す
                excel_bytes, pdf_bytes = generate_salary_excel_pdf_full(
                    staff.name,
                    safe_result,
                    selected_month_str,
                    detail_df   # ← ここを修正
                )

                # excel_bytes, pdf_bytes = generate_salary_excel_pdf_full(staff.name, safe_result, selected_month_str, detail_rows)
                detail_df = pd.DataFrame(detail_rows)

                
                b1, b2 = st.columns(2)
                with b1:
                    st.download_button(
                        "Excel出力",
                        excel_bytes,
                        file_name=f"{staff.name}_{selected_month_str}_salary.xlsx"
                    )
                with b2:
                    st.download_button(
                        "PDF出力",
                        pdf_bytes,
                        file_name=f"{staff.name}_{selected_month_str}_salary.pdf"
                    )
                    
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