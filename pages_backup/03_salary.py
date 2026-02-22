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
        selected_month = st.selectbox("", generate_month_options())

    staff = next(s for s in staff_list if s.name == selected_name)

    # =====================================================
    # 売上取得
    # =====================================================
    summary = SalesService.get_monthly_sales_summary_by_staff(
        staff_id=staff.id,
        target_month=selected_month
    )

    if summary["total_sales"] == 0:
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

    # KPI（超シンプル）
    col_left, col_right = st.columns([0.6, 0.4])  # 60% 左, 40% 右

    with col_left:
        st.markdown('<div class="total-label">総支給額</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="total-value"><span>¥</span>{int(result["total"]):,}</div>',
            unsafe_allow_html=True
        )

    with col_right:
        st.markdown(
            f'''
            <div class="drink-wrapper">
                <div class="mini-card">ドリンクバック</div>
                <div class="mini-value">¥{int(result["drink_back_amount"]):,}</div>
            </div>
            ''',
            unsafe_allow_html=True
        )

    # 明細
    colA, colB = st.columns([0.6, 0.4])

    with colA:
        st.markdown('<div class="section-title">給与内訳</div>', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        if result["type"] == "staff":
            col1.metric("組織売上", f"¥{int(result['org_sales']):,}")
            col2.metric("歩合率", f"{result['commission_rate']*100:.1f}%")
            col3.metric("歩合金額", f"¥{int(result['commission_amount']):,}")
            col4.metric("固定給", f"¥{int(result.get('fixed_salary',0)):,}")

    with colB:
        if result.get("drink_back_detail"):
            st.markdown('<div class="section-title">ドリンク内訳</div>', unsafe_allow_html=True)

            cols = st.columns(len(result["drink_back_detail"]))

            for i, (category, amount) in enumerate(result["drink_back_detail"].items()):
                cols[i].metric(category, f"¥{int(amount):,}")

    st.markdown("### 組織売上明細")

    detail_rows = []

    # -----------------------------
    # ① 本人売上
    # -----------------------------
    own_sales = SalesRepository.find_by_staff_and_month(
        staff.id,
        selected_month
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

    # カテゴリを辞書化
    category_map = category_master  # JSONそのまま辞書として使う


    # -----------------------------
    # ② 子担当者売上（drink_back_flg=1 除外）
    # -----------------------------
    children = [
        s for s in staff_list
        if s.parents and staff.id in s.parents
    ]

    for child in children:

        child_sales = SalesRepository.find_by_staff_and_month(
            child.id,
            selected_month
        )

        parent_count = len(child.parents)
        allocation_rate = 1.0 if parent_count == 1 else 0.5

        for sale in child_sales:

            category_obj = category_map.get(sale.category)

            # 🔴 drink_back対象カテゴリは除外
            if category_obj and category_obj.get("drink_back_flg") == 1:
                continue

            detail_rows.append({
                "営業日": sale.sales_date,
                "担当者名": sale.staff_name,
                "カテゴリ": sale.category,
                "商品名": sale.product_name,
                "売上": sale.amount,
                "親分配率": f"{int(allocation_rate*100)}%",
                "計上額": int(sale.amount * allocation_rate)
            })




    # -----------------------------
    # 表示
    # -----------------------------
    if detail_rows:

        # 日付降順
        detail_rows.sort(key=lambda x: x["営業日"], reverse=True)

        st.dataframe(detail_rows, use_container_width=True)

    else:
        st.info("該当する売上明細なし")


    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 給与確定管理
    # ==========================================
    confirm_data = SalaryConfirmRepository.find(
        staff.id,
        selected_month
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
            file_name=f"{staff.name}_{selected_month}_salary.xlsx",
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
        elements.append(Paragraph(f"対象月：{selected_month}", normal_style))
        elements.append(Spacer(1, 12))

        # ===== 明細テーブル =====
        data = [
            ["項目", "金額"],
            ["総売上", f"¥{int(result.get('org_sales',0)):,}"],
            ["歩合金額", f"¥{int(result.get('commission_amount',0)):,}"],
            ["固定給", f"¥{int(result.get('fixed_salary',0)):,}"],
            ["ドリンクバック", f"¥{int(result.get('drink_back_amount',0)):,}"],
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
            file_name=f"{staff.name}_{selected_month}_salary.pdf",
            use_container_width=True
        )

        st.download_button(
            "給料明細 出力",
            pdf_buffer.getvalue(),
            file_name=f"{staff.name}_{selected_month}_salary.pdf",
            use_container_width=True
        )

        st.download_button(
            "給料明細.出力",
            pdf_buffer.getvalue(),
            file_name=f"{staff.name}_{selected_month}_salary.pdf",
            use_container_width=True
        )

    else:
        from repositories.salary_repository import SalaryRepository
        from datetime import datetime

        year = st.number_input("年", value=datetime.now().year)
        month = st.number_input("月", value=datetime.now().month)

        if st.button("給与確定"):

            total_amount = int(result["total"])

            SalaryRepository.save_confirmed_salary(
                staff_id=staff.id,
                year=int(selected_month.split("-")[0]),
                month=int(selected_month.split("-")[1]),
                amount=total_amount
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

    st.markdown("<br>", unsafe_allow_html=True)

    # ----------------------------
    # ヘッダー
    # ----------------------------
    h1, h2, h3, h4, h5 = st.columns([2,1,2,1,2])

    h1.markdown('<div class="status-header">担当者</div>', unsafe_allow_html=True)
    h2.markdown('<div class="status-header">月</div>', unsafe_allow_html=True)
    h3.markdown('<div class="status-header">総支給額</div>', unsafe_allow_html=True)
    h4.markdown('<div class="status-header">状態</div>', unsafe_allow_html=True)
    h5.markdown('<div class="status-header">操作</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ----------------------------
    # 各担当者
    # ----------------------------
    for staff in staff_list:

        summary = SalesService.get_monthly_sales_summary_by_staff(
            staff_id=staff.id,
            target_month=selected_month_status
        )

        if summary["total_sales"] == 0:
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
            selected_month_status
        )

        col1, col2, col3, col4, col5 = st.columns([2,1,2,1,2])
        row_class = "status-row status-row-confirmed" if confirm else "status-row"

        with col1:
            st.markdown(
                f'<div class="{row_class}">{staff.name}</div>',
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f'<div class="{row_class}">{selected_month_status}</div>',
                unsafe_allow_html=True
            )

        with col3:
            amount_text = f"¥{int(total):,}" if total != "-" else "-"
            st.markdown(
                f'<div class="{row_class} status-amount">{amount_text}</div>',
                unsafe_allow_html=True
            )

        with col4:
            if confirm:
                st.markdown(
                    '<div class="{row_class} status-confirmed">● 確定済</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div class="{row_class} status-unconfirmed">● 未確定</div>',
                    unsafe_allow_html=True
                )

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