import streamlit as st
def main():
    import streamlit as st
    from datetime import datetime
    from repositories.staff_repository import StaffRepository
    from repositories.category_repository import CategoryRepository
    from repositories.salary_rule_repository import SalaryRuleRepository
    from services.salary_service import SalaryService
    from services.sales_service import SalesService
    from services.org_sales_detail_service import OrgSalesDetailService
    from repositories.sales_repository import SalesRepository
    import pandas as pd
    from io import BytesIO
    from repositories.salary_confirm_repository import SalaryConfirmRepository

    from ui.ui_style import apply_global_style
    apply_global_style()

    # =====================================================
    # 👑 ULTRA LUXURY BLACK THEME
    # =====================================================
    st.markdown("""
    <style>

    /* =====================================
    LAYOUT 統一（他ページと完全一致）
    ===================================== */
    .block-container {
        padding-top: 2.2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    /* Sticky Header */
    .sticky-header {
        position: sticky;
        top: 0;
        background-color: #0e1117;
        z-index: 999;
        padding-top: 10px;
        padding-bottom: 10px;
        border-bottom: 1px solid #333;
    }

    /* =====================================
    Apple Pro Compact
    ===================================== */
    html, body, [class*="css"] {
        background-color: #111317 !important;
        color: #f2f2f2 !important;
        font-family: -apple-system, BlinkMacSystemFont,
                    "SF Pro Display", "Hiragino Kaku Gothic ProN",
                    "Inter", sans-serif;
    }

    h1 {
        font-weight: 600;
        font-size: 20px;
        letter-spacing: 0.2px;
        margin-bottom: 1.4rem;
    }

    /* =====================================
    総支給エリア
    ===================================== */

    .total-label {
        font-size: 12px;
        color: #8b949e;
        letter-spacing: 0.6px;
    }

    .total-value {
        font-size: 50px;
        font-weight: 600;
        margin-top: 4px;
        letter-spacing: -0.5px;
    }

    .total-value span {
        font-size: 18px;
        margin-right: 4px;
        opacity: 0.6;
    }

    /* ドリンクバック */
    .mini-card {
        font-size: 12px;
        color: #8b949e;
        margin-top: 4px;
    }

    .mini-value {
        font-size: 22px;
        font-weight: 600;
    }

    /* =====================================
    セクション
    ===================================== */

    .section-title {
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 8px;
        margin-top: 24px;
        color: #9aa4b2;
    }

    /* =====================================
    metricカード（超圧縮）
    ===================================== */

    div[data-testid="stMetric"] {
        background: #1c1f26;
        padding: 14px;
        border-radius: 14px;
        border: 1px solid #2a2f38;
        margin-bottom: 10px;
        transition: 0.15s ease;
    }

    div[data-testid="stMetric"] label {
        font-size: 11px !important;
        color: #9aa4b2 !important;
    }

    div[data-testid="stMetric"] div {
        font-size: 16px !important;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border: 1px solid #3a3f4a;
    }

    /* =====================================
    ボタン
    ===================================== */

    .stButton > button {
        background: #1c1f26;
        border: 1px solid #2a2f38;
        border-radius: 12px;
        height: 42px;
        font-weight: 600;
        font-size: 13px;
    }

    .stButton > button:hover {
        background: #232733;
    }

    /* ==============================
    HEADER（存在感ある見出し）
    ============================== */

    .status-header {
        font-size: 16px;
        font-weight: 600;
        color: #e6edf3;
        letter-spacing: 0.6px;
        padding-bottom: 10px;
        border-bottom: 1px solid #2f3542;
    }

    /* ==============================
    ROW CARD（高級仕様）
    ============================== */

    .status-row {
        background: linear-gradient(145deg, #1c1f26, #181b21);
        padding: 18px 18px;
        border-radius: 18px;
        border: 1px solid #2a2f38;
        margin-bottom: 14px;
        min-height: 70px;
        display: flex;
        align-items: center;
        transition: all 0.2s ease;
    }

    .status-row:hover {
        border: 1px solid #3b4252;
        box-shadow: 0 4px 18px rgba(0,0,0,0.4);
        transform: translateY(-3px);
    }

    /* ==============================
    金額強調
    ============================== */

    .status-amount {
        font-weight: 600;
        font-size: 18px;
        letter-spacing: 0.3px;
    }

    /* ==============================
    状態表示
    ============================== */

    .status-confirmed {
        color: #34d399;
        font-weight: 600;
        letter-spacing: 0.3px;
    }

    .status-unconfirmed {
        color: #f87171;
        font-weight: 600;
        letter-spacing: 0.3px;
    }

    /* ==============================
    ボタンを横並びで美しく
    ============================== */

    div[data-testid="column"] .stDownloadButton > button {
        height: 40px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 13px;
    }
                
    /* ==============================
    確定済 背景トーン（上品な緑）
    ============================== */

    .status-row-confirmed {
        background: linear-gradient(
            145deg,
            rgba(34, 197, 94, 0.08),
            rgba(16, 185, 129, 0.05)
        );
        border: 1px solid rgba(52, 211, 153, 0.25);
    }

    .status-row-confirmed:hover {
        box-shadow: 0 4px 22px rgba(34, 197, 94, 0.15);
    }

    /* 未確定は通常トーン維持 */

    </style>
    """, unsafe_allow_html=True)



    st.title("💰給与管理")

    tab1, tab2 = st.tabs(["給与確認", "状態確認"])

    with tab1:
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
        # 月生成
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
        # フィルター
        # =====================================================
        col1, col2 = st.columns([0.6, 0.4])

        with col1:
            selected_name = st.selectbox("", [s.name for s in staff_list])

        with col2:
            selected_month_str = st.selectbox("", generate_month_options())

        # 🔥 ここで一度だけ分解
        year, month = map(int, selected_month_str.split("-"))

        staff = next(s for s in staff_list if s.name == selected_name)

        staff = next(s for s in staff_list if s.name == selected_name)

        # =====================================================
        # 売上取得
        # =====================================================
        summary = SalesService.get_monthly_sales_summary_by_staff(
            staff_id=staff.id,
            target_month=selected_month_str
        )

        if summary.get("personal_sales_amount", 0) == 0 and \
        summary.get("children_sales_amount", 0) == 0:
            st.warning("この月の売上データがありません")
            st.stop()

        # =====================================================
        # 給与計算
        # =====================================================
        if staff.type == "staff":
            result = SalaryService.calculate_staff_salary(
                staff,
                summary,
                salary_rules.get("commission_rules", []),
                category_master
            )
        else:
            result = SalaryService.calculate_part_time_salary(
                staff,
                summary,
                category_master
            )

        # UI側（03_給与計算.py）

        # =====================================================
        # 上段：総支給額（右削除）
        # =====================================================

        org_f = summary.get("org_sales_f", 0)
        commission_rate = result.get("commission_rate", 0)
        st.markdown(
        """
        <div class="total-wrapper">
        <div class="total-main-label">総支給額</div>
        <div class="total-value">¥{:,}</div>
        <div class="total-meta">
        F: {:,} / Rate: {:.1f}%
        </div>
        </div>
        """.format(
            int(result["total"]),
            int(org_f),
            commission_rate * 100
        ),
        unsafe_allow_html=True
        )
        

        col_left = st.container()

        # with col_left:
        #     st.markdown('<div class="total-label">総支給額</div>', unsafe_allow_html=True)
        #     st.markdown(
        #         f'<div class="total-value"><span>¥</span>{int(result["total"]):,}</div>',
        #         unsafe_allow_html=True
        #     )

        # =====================================================
        # 給与内訳＋報酬条件（横一列）
        # =====================================================

        st.markdown('<div class="section-title">給与内訳</div>', unsafe_allow_html=True)

        # 6列で横並び
        c1, c2, c3, c4, c5, c6 = st.columns(6)

        personal_amount = summary.get("personal_sales_amount", 0)
        personal_f = summary.get("personal_sales_f", 0)
        org_amount = summary.get("org_sales_amount", personal_amount)
        org_f = summary.get("org_sales_f", 0)
        commission_rate = result.get("commission_rate", 0)

        c1.metric("個人売上金額", f"¥{int(personal_amount):,}")
        c2.metric("個人売上F", f"{int(personal_f):,}")
        c3.metric("組織売上金額", f"¥{int(org_amount):,}")
        c4.metric("組織売上F", f"{int(org_f):,}")
        c5.metric("レート", f"{commission_rate*100:.1f}%")

        if staff.type == "staff":
            c6.metric("家賃", "¥2,000")
        else:
            c6.metric("家賃", "-")


        # =====================================================
        # 組織売上明細
        # =====================================================

        st.markdown("### 組織売上明細")

        detail_rows = []

        # ① 本人売上
        own_sales = SalesRepository.find_by_staff_and_month(
            staff.id,
            selected_month_str
        )

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


        # ② 子担当者売上
        children = [
            s for s in staff_list
            if s.parents and staff.id in s.parents
        ]

        for child in children:

            child_sales = SalesRepository.find_by_staff_and_month(
                child.id,
                selected_month_str
            )

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


        # 表示
        if detail_rows:
            detail_rows.sort(key=lambda x: x["営業日"], reverse=True)
            st.dataframe(detail_rows, use_container_width=True)
        else:
            st.info("該当する売上明細なし")


        st.markdown("<br>", unsafe_allow_html=True)

        # ==========================================
        # 給与確定管理
        # ==========================================
        from datetime import datetime

        col1, col2 = st.columns(2)

        
        confirm_data = SalaryConfirmRepository.find(
            staff.id,
            year,
            month
        )

        if confirm_data:

            st.success("✅ 給与確定処理が完了しました")

            # -----------------------
            # 再出力
            # -----------------------
            df_export = pd.DataFrame(detail_rows)

            # Excel
            excel_buffer = BytesIO()
            df_export.to_excel(excel_buffer, index=False)

            st.download_button(
                "Excel明細出力",
                excel_buffer.getvalue(),
                file_name=f"{staff.name}_{month}_salary.xlsx",
                use_container_width=True
            )

            # PDF（簡易版）
            # PDF（本物）
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            from reportlab.pdfbase import pdfmetrics
            from io import BytesIO

            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)

            elements = []

            # 🔥 日本語CIDフォント登録（必須）
            pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))

            # 🔥 スタイルを明示的に日本語フォントにする
            title_style = ParagraphStyle(
                name="TitleJP",
                fontName="HeiseiKakuGo-W5",
                fontSize=16,
                spaceAfter=12,
            )

            normal_style = ParagraphStyle(
                name="NormalJP",
                fontName="HeiseiKakuGo-W5",
                fontSize=11,
            )

            elements.append(Paragraph("給与明細書", title_style))
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"担当者：{staff.name}", normal_style))
            elements.append(Paragraph(f"対象月：{month}", normal_style))
            elements.append(Spacer(1, 12))

            # ===== 明細テーブル =====
            data = data = [
                ["項目", "金額"],
                ["個人売上金額", f"¥{int(personal_amount):,}"],
                ["個人売上F", f"{int(personal_f):,}"],
                ["組織売上金額", f"¥{int(org_amount):,}"],
                ["組織売上F", f"{int(org_f):,}"],
                ["報酬レート", f"{commission_rate*100:.1f}%"],
                ["家賃", "¥2,000" if staff.type == "staff" else "-"],
                ["総支給額", f"¥{int(result['total']):,}"],
            ]

            table = Table(data, colWidths=[80*mm, 40*mm])

            table.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,-1), 'HeiseiKakuGo-W5'),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
            ]))

            elements.append(table)

            doc.build(elements)

            st.download_button(
                "給与明細PDF",
                pdf_buffer.getvalue(),
                file_name=f"{staff.name}_{month}_salary.pdf",
                use_container_width=True
            )

        else:
            from repositories.salary_repository import SalaryRepository
            from datetime import datetime


            from repositories.salary_confirm_repository import SalaryConfirmRepository

            # ==========================================
            # 給与確定管理
            # ==========================================

            confirm_data = SalaryConfirmRepository.find(
                staff.id,
                year,
                month
            )

            if confirm_data:

                st.success("✅ 給与確定済")

            else:
                if st.button("給与確定"):

                    total_amount = int(result.get("total", 0))

                    SalaryConfirmRepository.confirm(
                        staff_id=staff.id,
                        year=year,
                        month=month,
                        total=total_amount
                    )

                    st.success("給与を確定しました")
                    st.rerun()        

    # # =====================================================
    # ■ 状態確認タブ（再出力対応版）
    # =====================================================
    with tab2:

        st.markdown("### 給与確定状況一覧")

        selected_month_status = st.selectbox(
            "対象月",
            generate_month_options(),
            key="status_month"
        )

        # 🔥 ここで分解（1回のみ）
        year_status, month_status = map(
            int,
            selected_month_status.split("-")
        )

        st.markdown("<br>", unsafe_allow_html=True)

        for staff in staff_list:

            summary = SalesService.get_monthly_sales_summary_by_staff(
                staff_id=staff.id,
                target_month=selected_month_status
            )

            if summary["org_sales_f"] == 0:
                total = "-"
                result = None
            else:
                if staff.type == "staff":
                    result = SalaryService.calculate_staff_salary(
                        staff,
                        summary,
                        salary_rules.get("commission_rules", []),
                        category_master
                    )
                else:
                    result = SalaryService.calculate_part_time_salary(
                        staff,
                        summary,
                        category_master
                    )

                total = result["total"]

            confirm = SalaryConfirmRepository.find(
                staff.id,
                year_status,
                month_status
            )

            col1, col2, col3, col4, col5 = st.columns([2,1,2,1,2])
            row_class = "status-row status-row-confirmed" if confirm else "status-row"

            with col1:
                st.write(staff.name)

            with col2:
                st.write(selected_month_status)

            with col3:
                st.write(f"¥{int(total):,}" if total != "-" else "-")

            with col4:
                if confirm:
                    st.success("確定済")
                else:
                    st.error("未確定")

            with col5:

                if confirm and result:

                    df_export = pd.DataFrame([{
                        "担当者": staff.name,
                        "対象月": selected_month_status,
                        "総支給額": total
                    }])

                    excel_buffer = BytesIO()
                    df_export.to_excel(excel_buffer, index=False)

                    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                    from reportlab.lib.styles import ParagraphStyle
                    from reportlab.lib import colors
                    from reportlab.lib.pagesizes import A4
                    from reportlab.lib.units import mm
                    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
                    from reportlab.pdfbase import pdfmetrics
                    from io import BytesIO

                    pdf_buffer = BytesIO()
                    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)

                    elements = []

                    # 🔥 日本語CIDフォント登録（必須）
                    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))

                    # 🔥 スタイルを明示的に日本語フォントにする
                    title_style = ParagraphStyle(
                        name="TitleJP",
                        fontName="HeiseiKakuGo-W5",
                        fontSize=16,
                        spaceAfter=12,
                    )

                    normal_style = ParagraphStyle(
                        name="NormalJP",
                        fontName="HeiseiKakuGo-W5",
                        fontSize=11,
                    )

                    doc.build(elements)

                    b1, b2 = st.columns(2)

                    with b1:
                        st.download_button(
                            "Excel",
                            excel_buffer.getvalue(),
                            file_name=f"{staff.name}_{selected_month_status}_salary.xlsx",
                            key=f"excel_{staff.id}",
                            use_container_width=True
                        )

                    with b2:
                        st.download_button(
                            "PDF",
                            pdf_buffer.getvalue(),
                            file_name=f"{staff.name}_{selected_month_status}_salary.pdf",
                            key=f"pdf_{staff.id}",
                            use_container_width=True
                        )

                else:
                    st.markdown(
                        '<div class="status-row">-</div>',
                        unsafe_allow_html=True
                    )

            st.markdown("<br>", unsafe_allow_html=True)