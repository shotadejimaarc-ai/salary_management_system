from ui.ui_style import apply_global_style
from ui.sidebar import render_sidebar

# 給与計算・確定.py
# Streamlit 給与計算画面
#   - Tab1: バイト給与（v_baito_salary）
#   - Tab2: スタッフ給与（v_staff_net_salary）
# 依存: streamlit, sqlalchemy, pandas

import json
from datetime import datetime, date

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
if not st.session_state.get("authenticated", False):
    st.switch_page("app.py")
GREEN = colors.HexColor("#2F5D2E")
LIGHT_ROW = colors.HexColor("#F3F5F3")
BORDER = colors.HexColor("#2F5D2E")


def _ensure_fonts():
    """
    日本語フォント登録（fonts/ 配下に配置が必要）
      - fonts/NotoSansJP-Regular.ttf
      - fonts/NotoSansJP-Bold.ttf (任意)
    """
    if "NotoSansJP" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("NotoSansJP", "fonts/NotoSansJP-Regular.ttf"))
    if "NotoSansJP-Bold" not in pdfmetrics.getRegisteredFontNames():
        try:
            pdfmetrics.registerFont(TTFont("NotoSansJP-Bold", "fonts/NotoSansJP-Bold.ttf"))
        except Exception:
            pass


def _set_font(c: canvas.Canvas, size: int = 10, bold: bool = False):
    if bold and ("NotoSansJP-Bold" in pdfmetrics.getRegisteredFontNames()):
        c.setFont("NotoSansJP-Bold", size)
    else:
        c.setFont("NotoSansJP", size)


def _fmt_money_or_text(v) -> str:
    """
    右側表示用：
    - str ならそのまま（例 '55.0%'）
    - 数値なら ¥付き
    """
    if isinstance(v, str):
        return v
    try:
        return f"¥{int(round(float(v))):,}"
    except Exception:
        return "¥0"


def _safe_label_amount(item) -> tuple[str, object]:
    """
    items の形が崩れても落ちないように正規化
    - ("適用レート", "55.0%")
    - ("家賃", 20000)
    - "メモだけ" 等にも耐える
    """
    if not isinstance(item, (list, tuple)):
        return str(item), ""
    if len(item) == 0:
        return "", ""
    if len(item) == 1:
        return str(item[0]), ""
    # 2個以上なら先頭2つだけ
    return str(item[0]), item[1]


def build_payslip_pdf_like_template(
    *,
    company_name: str,
    target_month_ym: str,   # "YYYY-MM"
    staff_no: str,
    name: str,
    staff_type: str,        # "staff" or "baito"
    net_amount: int,        # 差引支給額
    left_items: list,       # [(label, amount_or_text), ...]
    right_items: list,      # [(label, amount_or_text), ...]
    left_footer_amount=None,   # ★支給総額を「報酬額」にしたい時にここで上書きできる
) -> bytes:
    _ensure_fonts()

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    # ===== 基本レイアウト =====
    page_left = 14 * mm
    page_right = 14 * mm
    content_w = W - page_left - page_right
    y = H - 18 * mm

    # ===== ヘッダー緑帯 =====
    header_h = 14 * mm
    c.setFillColor(GREEN)
    c.rect(page_left, y - header_h, content_w, header_h, stroke=0, fill=1)

    _set_font(c, 10, bold=True)
    c.setFillColor(colors.white)
    c.drawString(page_left + 8 * mm, y - header_h + 4 * mm, f"{company_name}　給与明細")
    _set_font(c, 9, bold=True)
    c.drawRightString(page_left + content_w - 8 * mm, y - header_h + 4 * mm, f"{target_month_ym}分")

    y -= (header_h + 6 * mm)

    # ===== 社員NO / 氏名 =====
    box_h = 8 * mm
    label_w = 26 * mm
    value_w = 55 * mm

    c.setFillColor(GREEN)
    c.rect(page_left, y - box_h, label_w, box_h, stroke=0, fill=1)
    _set_font(c, 8, bold=True)
    c.setFillColor(colors.white)
    c.drawString(page_left + 3 * mm, y - box_h + 2.2 * mm, "社員NO.")

    c.setFillColor(colors.white)
    c.setStrokeColor(BORDER)
    c.rect(page_left + label_w, y - box_h, value_w, box_h, stroke=1, fill=1)
    _set_font(c, 9, bold=False)
    c.setFillColor(colors.black)
    c.drawString(page_left + label_w + 3 * mm, y - box_h + 2.2 * mm, str(staff_no))

    name_label_w = 16 * mm
    name_value_w = 70 * mm
    x2 = page_left + label_w + value_w + 10 * mm

    c.setFillColor(GREEN)
    c.rect(x2, y - box_h, name_label_w, box_h, stroke=0, fill=1)
    _set_font(c, 8, bold=True)
    c.setFillColor(colors.white)
    c.drawString(x2 + 3 * mm, y - box_h + 2.2 * mm, "氏名")

    c.setFillColor(colors.white)
    c.setStrokeColor(BORDER)
    c.rect(x2 + name_label_w, y - box_h, name_value_w, box_h, stroke=1, fill=1)
    _set_font(c, 9, bold=False)
    c.setFillColor(colors.black)
    c.drawString(x2 + name_label_w + 3 * mm, y - box_h + 2.2 * mm, str(name))

    y -= (box_h + 8 * mm)

    # ===== 差引支給額 =====
    pay_label_w = 34 * mm
    pay_value_w = 52 * mm
    pay_h = 10 * mm

    c.setFillColor(GREEN)
    c.rect(page_left, y - pay_h, pay_label_w, pay_h, stroke=0, fill=1)
    _set_font(c, 8, bold=True)
    c.setFillColor(colors.white)
    c.drawString(page_left + 3 * mm, y - pay_h + 3 * mm, "差引支給額")

    c.setFillColor(colors.white)
    c.setStrokeColor(BORDER)
    c.rect(page_left + pay_label_w, y - pay_h, pay_value_w, pay_h, stroke=1, fill=1)
    _set_font(c, 11, bold=True)
    c.setFillColor(colors.black)
    c.drawRightString(page_left + pay_label_w + pay_value_w - 3 * mm, y - pay_h + 2.6 * mm, _fmt_money_or_text(net_amount))

    y -= (pay_h + 10 * mm)

    # ===== 左右テーブル =====
    gap = 10 * mm
    col_w = (content_w - gap) / 2
    table_h = 150 * mm
    row_h = 8.5 * mm
    header_row_h = 9 * mm
    footer_row_h = 9 * mm

    x_left = page_left
    x_right = page_left + col_w + gap
    y_top = y

    def calc_numeric_sum(items):
        s = 0.0
        for it in items:
            _, a = _safe_label_amount(it)
            # 数値だけ合算（%など文字は除外）
            if isinstance(a, str):
                continue
            try:
                s += float(a or 0)
            except Exception:
                pass
        return s

    def draw_table(x, title, items, footer_label, footer_amount, show_amount=True):
        # 外枠
        c.setStrokeColor(BORDER)
        c.setFillColor(colors.white)
        c.rect(x, y_top - table_h, col_w, table_h, stroke=1, fill=1)

        # ヘッダー
        c.setFillColor(GREEN)
        c.rect(x, y_top - header_row_h, col_w, header_row_h, stroke=0, fill=1)
        _set_font(c, 9, bold=True)
        c.setFillColor(colors.white)
        c.drawCentredString(x + col_w / 2, y_top - header_row_h + 2.6 * mm, title)

        # 本文
        body_y = y_top - header_row_h
        usable_h = table_h - header_row_h - footer_row_h
        max_rows = int(usable_h / row_h)

        # 交互背景
        for i in range(max_rows):
            if i % 2 == 1:
                c.setFillColor(LIGHT_ROW)
                c.rect(x, body_y - (i + 1) * row_h, col_w, row_h, stroke=0, fill=1)

        label_x = x + 4 * mm
        amt_x = x + col_w - 4 * mm

        _set_font(c, 9, bold=False)
        c.setFillColor(colors.black)

        for i in range(min(len(items), max_rows)):
            label, amount = _safe_label_amount(items[i])
            yy = body_y - (i + 1) * row_h + 2.2 * mm
            c.drawString(label_x, yy, label)
            if show_amount:
                c.drawRightString(amt_x, yy, _fmt_money_or_text(amount))

        # 仕切り線
        c.setStrokeColor(BORDER)
        c.line(x + col_w * 0.68, y_top - header_row_h, x + col_w * 0.68, y_top - table_h + footer_row_h)

        # フッター
        c.setFillColor(GREEN)
        c.rect(x, y_top - table_h, col_w, footer_row_h, stroke=0, fill=1)
        _set_font(c, 8, bold=True)
        c.setFillColor(colors.white)
        c.drawString(x + 3 * mm, y_top - table_h + 2.6 * mm, footer_label)
        c.drawRightString(x + col_w - 3 * mm, y_top - table_h + 2.6 * mm, _fmt_money_or_text(footer_amount))

    # フッター合計
    computed_left_total = calc_numeric_sum(left_items)
    computed_right_total = calc_numeric_sum(right_items)

    # ★支給総額を外から上書きできる（スタッフなら報酬額にしたい）
    left_total = left_footer_amount if left_footer_amount is not None else computed_left_total
    right_total = computed_right_total

    draw_table(x_left, "支給", left_items, "支給総額", left_total, show_amount=True)

    if staff_type == "staff":
        draw_table(x_right, "控除", right_items, "控除総額", right_total, show_amount=True)

    # フッター（区分）
    _set_font(c, 7, bold=False)
    c.setFillColor(colors.HexColor("#666666"))
    c.drawRightString(page_left + content_w, 10 * mm, f"区分：{'バイト' if staff_type=='baito' else 'スタッフ'}")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()

st.set_page_config(page_title="給与計算", layout="wide")
st.markdown(
    """
<style>
.block-container{
  padding-top: 4.2rem !important;
  padding-left: 1.2rem;
  padding-right: 1.2rem;
  max-width: 1400px;
}
.big-title{ font-size: 2.2rem; font-weight: 900; margin: 0 0 0.2rem 0; }
.subtle{ color: rgba(255,255,255,0.68); margin-bottom: 0.8rem; }
.card{
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 14px;
  padding: 1rem 1rem;
  background: rgba(255,255,255,0.03);
}
hr{ border: none; border-top: 1px solid rgba(255,255,255,0.12); margin: 1.0rem 0; }
</style>
""",
    unsafe_allow_html=True,
)

if "payslip_pdf" not in st.session_state:
    st.session_state["payslip_pdf"] = None
if "payslip_filename" not in st.session_state:
    st.session_state["payslip_filename"] = None

# =========================
# DB
# =========================
@st.cache_resource
def get_engine():
    db_url = None
    try:
        db_url = st.secrets["DATABASE_URL"]
    except Exception:
        pass

    if not db_url:
        import os
        db_url = os.getenv("DATABASE_URL")

    if not db_url:
        st.error("DATABASE_URL が未設定です（secrets または環境変数）")
        st.stop()

    return create_engine(db_url, pool_pre_ping=True)

engine = get_engine()

def fetch_df(sql: str, params: dict | None = None) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})

def exec_sql(sql: str, params: dict | None = None):
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})

def table_has_column(table_name: str, column_name: str) -> bool:
    q = """
    select 1
    from information_schema.columns
    where table_schema='public'
      and table_name=:t
      and column_name=:c
    limit 1
    """
    df = fetch_df(q, {"t": table_name, "c": column_name})
    return len(df) > 0

from io import BytesIO

def export_org_detail_excel_staff(staff_id: str, target_month_ym: str) -> bytes:
    sql = """
    WITH RECURSIVE org AS (
      SELECT s.staff_id::text AS staff_id,
             1.0::numeric    AS w
      FROM public.staff s
      WHERE s.staff_id::text = :sid

      UNION ALL

      SELECT c.staff_id::text AS staff_id,
             org.w *
             CASE
               WHEN c.parent_id IS NOT NULL AND c.parent_id_2 IS NOT NULL THEN 0.5::numeric
               ELSE 1.0::numeric
             END AS w
      FROM public.staff c
      JOIN org
        ON (c.parent_id::text = org.staff_id OR c.parent_id_2::text = org.staff_id)
    ),
    staff_weights AS (
      SELECT staff_id,
             LEAST(SUM(w), 1.0)::numeric AS weight_share
      FROM org
      GROUP BY staff_id
    )
    SELECT
      e.created_at::date                             AS "営業日",
      s.name                                         AS "担当者名",
      e.category_name                                AS "カテゴリ",
      e.menu_name                                    AS "メニュー",
      e.unit_price                                   AS "単価",
      e.qty                                          AS "数量",
      e.amount                                       AS "金額",
      COALESCE(e.f_rate, 0)                          AS "F値",
      ROUND(e.amount * COALESCE(e.f_rate, 0) * w.weight_share)::bigint AS "売上F"
    FROM public.v_order_items_enriched e
    JOIN staff_weights w
      ON w.staff_id = e.staff_id::text
    LEFT JOIN public.staff s
      ON s.staff_id::text = e.staff_id::text
    WHERE e.target_month = :ym
    ORDER BY e.created_at, s.name, e.category_name, e.menu_name;
    """

    df = fetch_df(sql, {"sid": str(staff_id), "ym": target_month_ym})

    out = BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="明細")
    out.seek(0)
    return out.read()

# # =========================
# # 全銀CSV（GMOあおぞら向けのベース）
# # =========================
# def to_kana(s: str) -> str:
#     return s or ""

# def pad_left(s: str, width: int, fill="0") -> str:
#     s = str(s or "")
#     return s.rjust(width, fill)[:width]

# def zengin_transfer_csv(rows: list[dict], header_info: dict) -> str:
#     lines = []
#     lines.append(",".join([
#         "1",
#         header_info.get("client_code", ""),
#         header_info.get("client_name_kana", ""),
#         header_info.get("transfer_date", ""),
#         header_info.get("debit_bank_code", ""),
#         header_info.get("debit_branch_code", ""),
#         header_info.get("debit_account_type", ""),
#         header_info.get("debit_account_number", ""),
#         header_info.get("debit_account_holder", ""),
#     ]))

#     total_cnt = 0
#     total_amount = 0

#     for r in rows:
#         total_cnt += 1
#         amt = int(r["amount"])
#         total_amount += amt
#         lines.append(",".join([
#             "2",
#             pad_left(r["bank_code"], 4),
#             pad_left(r["branch_code"], 3),
#             str(r.get("account_type") or ""),
#             pad_left(r["account_number"], 7),
#             to_kana(r["account_holder"]),
#             str(amt),
#             r.get("name", ""),
#         ]))

#     lines.append(",".join(["8", str(total_cnt), str(total_amount)]))
#     lines.append("9")
#     return "\n".join(lines)

# =========================
# ユーティリティ
# =========================
def yen(x):
    try:
        return int(round(float(x)))
    except Exception:
        return 0

# =========================
# UI
# =========================
st.title("💴給与計算")
if st.session_state.get("payslip_pdf"):
    st.download_button(
        "📄 直前に確定した給与明細PDFをダウンロード",
        data=st.session_state["payslip_pdf"],
        file_name=st.session_state.get("payslip_filename") or "給与明細.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
    # 1回出したら消す（連続で欲しいなら消さなくてもOK）
    # st.session_state["payslip_pdf"] = None
    # st.session_state["payslip_filename"] = None

# -------------------------
# 対象月リスト（スタッフ＋バイトの union）
# -------------------------
months_df = fetch_df("""
select distinct target_month
from (
  select target_month from public.v_staff_net_salary where target_month is not null
  union
  select target_month from public.v_baito_salary where target_month is not null
) t
order by target_month desc
""")

if months_df.empty:
    st.warning("対象月データがありません（v_staff_net_salary / v_baito_salary）。")
    st.stop()

month_options = []
for m in months_df["target_month"].tolist():
    if hasattr(m, "strftime"):
        month_options.append(m.strftime("%Y-%m"))
    else:
        s = str(m)
        month_options.append(s[:7])

# 重複排除（順序維持）
seen = set()
month_options = [x for x in month_options if not (x in seen or seen.add(x))]

target_month_ym = st.selectbox("対象月", month_options)
target_month_date: date = datetime.strptime(target_month_ym + "-01", "%Y-%m-%d").date()

tab_baito, tab_staff, tab_confirms = st.tabs(["バイト給与", "スタッフ給与", "✅ 確定情報"])

# =========================
# 確定情報（共通）
# =========================
confirm_df = fetch_df("""
select staff_id, staff_type, target_month, total_amount, confirmed_at
from public.salary_confirms
where target_month = :m
""", {"m": target_month_date})

confirmed_staff = {r["staff_id"]: r for _, r in confirm_df[confirm_df["staff_type"]=="staff"].iterrows()} if not confirm_df.empty else {}
confirmed_baito = {r["staff_id"]: r for _, r in confirm_df[confirm_df["staff_type"]=="baito"].iterrows()} if not confirm_df.empty else {}

# =========================
# Tab1: バイト給与
# =========================
with tab_baito:
    baito_df = fetch_df("""
    select
      staff_id,
      name,
      target_month,
      hourly_wage,
      total_hours,
      transport_one_way,
      attendance_days,
      drinkback_total,
      hourly_salary,
      transport_total,
      total_salary
    from public.v_baito_salary
    where target_month = :m
    order by total_salary desc
    """, {"m": target_month_date})

    left, right = st.columns([3, 2])

    with left:
        st.subheader("バイト別 給与一覧（計算結果）")

        if baito_df.empty:
            st.info("対象月にバイトデータがありません。")
        else:
            view_df = baito_df.copy()
            view_df["confirmed"] = view_df["staff_id"].apply(lambda sid: "✅" if sid in confirmed_baito else "")

            money_cols = ["hourly_wage","transport_one_way","drinkback_total","hourly_salary","transport_total","total_salary"]
            for c in money_cols:
                if c in view_df.columns:
                    view_df[c] = pd.to_numeric(view_df[c], errors="coerce").fillna(0)

            display_df = view_df.rename(columns={
                "confirmed":"確定",
                "name":"バイト名",
                "hourly_wage":"時給",
                "total_hours":"稼働時間",
                "attendance_days":"出勤日数",
                "drinkback_total":"ドリンクバック",
                "hourly_salary":"時給計",
                "transport_total":"交通費計",
                "total_salary":"総支給額",
            })

            show_cols = ["確定","バイト名","時給","稼働時間","出勤日数","ドリンクバック","時給計","交通費計","総支給額"]
            show_cols = [c for c in show_cols if c in display_df.columns]

            st.dataframe(
                display_df[show_cols],
                use_container_width=True,
                hide_index=True,
                height=560
            )

    with right:
        st.subheader("操作（バイト）")

        if baito_df.empty:
            st.info("左の一覧が空です。")
        else:
            names = baito_df["name"].tolist()
            selected_name = st.selectbox("バイトを選択", names, key="baito_select")

            row = baito_df[baito_df["name"] == selected_name].iloc[0].to_dict()
            staff_id = row["staff_id"]

            is_confirmed = staff_id in confirmed_baito
            if is_confirmed:
                c = confirmed_baito[staff_id]
                st.success(f"✅ 確定済（総額 ¥{int(c['total_amount']):,}）")
                st.caption(f"confirmed_at: {c['confirmed_at']}")
            else:
                st.info("未確定")

            st.markdown("### 給与内訳（バイト）")
            total_yen = yen(row.get("total_salary"))
            st.metric("総支給額", f"¥{total_yen:,}")

            st.write({
                "時給": yen(row.get("hourly_wage")),
                "稼働時間": float(row.get("total_hours") or 0),
                "時給計": yen(row.get("hourly_salary")),
                "交通費計": yen(row.get("transport_total")),
                "ドリンクバック": yen(row.get("drinkback_total")),
                "出勤日数": yen(row.get("attendance_days")),
            })

            st.markdown("### 給与確定・取消（バイト）")

            payment_method = "cash"  # バイトは現状固定（必要なら staff テーブルから取る）
            total_salary = yen(row.get("total_salary"))

            breakdown = {
                "target_month": target_month_date.isoformat(),
                "staff_id": staff_id,
                "staff_type": "baito",
                "inputs": {
                    "hourly_wage": float(row.get("hourly_wage") or 0),
                    "total_hours": float(row.get("total_hours") or 0),
                    "transport_one_way": float(row.get("transport_one_way") or 0),
                    "attendance_days": float(row.get("attendance_days") or 0),
                    "drinkback_total": float(row.get("drinkback_total") or 0),
                },
                "calc": {
                    "hourly_salary": float(row.get("hourly_salary") or 0),
                    "transport_total": float(row.get("transport_total") or 0),
                    "total_salary": float(row.get("total_salary") or 0),
                },
                "meta": {
                    "rule_version": "baito-v1",
                    "calculated_at": datetime.now().isoformat(timespec="seconds"),
                    "payment_method": payment_method,
                }
            }

            colA, colB = st.columns(2)

            with colA:
                if st.button("給与確定（バイト）", disabled=is_confirmed, key="confirm_baito"):
                    # DB確定
                    exec_sql("""
                    insert into public.salary_confirms
                    (target_month, staff_id, staff_type, total_amount, breakdown, confirmed_at)
                    values
                    (:tm, :sid, :stype, :total, CAST(:breakdown AS jsonb), now())
                    """, {
                        "tm": target_month_date,
                        "sid": staff_id,
                        "stype": "baito",
                        "total": total_salary,
                        "breakdown": json.dumps(breakdown, ensure_ascii=False),
                    })

                    # ===== PDF用の項目（あなた指定）=====
                    left_items = [
                        ("時給計", yen(row.get("hourly_salary"))),
                        ("交通費計", yen(row.get("transport_total"))),
                        ("ドリンクバック", yen(row.get("drinkback_total"))),
                    ]

                    pdf_bytes = build_payslip_pdf_like_template(
                        company_name="株式会社ＪＯＹ　ａｔ",
                        target_month_ym=target_month_ym,
                        staff_no=str(staff_id),
                        name=row["name"],
                        staff_type="baito",
                        net_amount=yen(row.get("total_salary")),
                        left_items=left_items,
                        right_items=[],
                    )

                    st.session_state["payslip_pdf"] = pdf_bytes
                    st.session_state["payslip_filename"] = f"給与明細_{target_month_ym}_{row['name']}_baito.pdf"

                    st.success("給与確定しました（バイト）")
                    st.rerun()
                    

            with colB:
                if st.button("給与取消（バイト）", disabled=not is_confirmed, key="cancel_baito"):
                    has_is_canceled = table_has_column("salary_confirms", "is_canceled")
                    if has_is_canceled:
                        exec_sql("""
                        update public.salary_confirms
                        set is_canceled = true, canceled_at = now()
                        where staff_id = :sid and staff_type='baito' and target_month = :tm
                        """, {"sid": staff_id, "tm": target_month_date})
                    else:
                        exec_sql("""
                        delete from public.salary_confirms
                        where staff_id = :sid and staff_type='baito' and target_month = :tm
                        """, {"sid": staff_id, "tm": target_month_date})

                    st.warning("給与取消しました（バイト）")
                    st.rerun()

# =========================
# Tab2: スタッフ給与（既存ロジック）
# =========================
with tab_staff:
    salary_df = fetch_df("""
    select
      staff_id,
      name,
      target_month,
      personal_sales,
      org_sales,
      personal_f,
      org_f,
      applied_rate,
      gross_reward,
      child_staff_deduction,
      child_baito_deduction,
      rent,
      total_salary
    from public.v_staff_net_salary
    where target_month = :m
    order by total_salary desc
    """, {"m": target_month_date})

    left, right = st.columns([3, 2])

    with left:
        st.subheader("スタッフ別 給与一覧（計算結果）")

        if salary_df.empty:
            st.info("対象月にスタッフデータがありません。")
        else:
            view_df = salary_df.copy()
            view_df["confirmed"] = view_df["staff_id"].apply(lambda sid: "✅" if sid in confirmed_staff else "")

            money_cols = [
                "personal_sales", "org_sales",
                "personal_f", "org_f",
                "gross_reward",
                "child_staff_deduction", "child_baito_deduction",
                "rent", "total_salary",
            ]
            for c in money_cols:
                if c in view_df.columns:
                    view_df[c] = pd.to_numeric(view_df[c], errors="coerce").fillna(0).round(0).astype(int)

            display_df = view_df.rename(columns={
                "confirmed": "確定",
                "name": "スタッフ名",
                "personal_sales": "個人売上",
                "org_sales": "組織売上",
                "personal_f": "個人F",
                "org_f": "組織F",
                "applied_rate": "適用レート",
                "gross_reward": "報酬額",
                "child_staff_deduction": "子staff控除",
                "child_baito_deduction": "子baito控除",
                "rent": "家賃",
                "total_salary": "総支給額",
            })

            show_cols = [
                "確定", "スタッフ名",
                "個人売上", "組織売上",
                "個人F", "組織F", "適用レート",
                "報酬額", "子staff控除", "子baito控除", "家賃",
                "総支給額",
            ]
            show_cols = [c for c in show_cols if c in display_df.columns]
            display_df = display_df[show_cols]

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=560
            )

    with right:
        st.subheader("操作（スタッフ）")

        staff_names = salary_df["name"].tolist()
        if not staff_names:
            st.info("対象月にスタッフデータがありません。")
        else:
            selected_name = st.selectbox("スタッフを選択", staff_names, key="staff_select")
            row = salary_df[salary_df["name"] == selected_name].iloc[0].to_dict()
            staff_id = row["staff_id"]

            st.markdown("### 組織売上 明細Excel")

            excel_bytes = export_org_detail_excel_staff(
                staff_id=str(staff_id),
                target_month_ym=target_month_ym
            )

            st.download_button(
                "📥 Excel出力",
                data=excel_bytes,
                file_name=f"組織売上明細_{target_month_ym}_{selected_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            is_confirmed = staff_id in confirmed_staff
            if is_confirmed:
                c = confirmed_staff[staff_id]
                st.success(f"✅ 確定済（総額 ¥{int(c['total_amount']):,}）")
                st.caption(f"confirmed_at: {c['confirmed_at']}")
            else:
                st.info("未確定")

            # =========================
            # 内訳（カード）
            # =========================
            st.markdown("### 給与内訳")

            personal_sales_yen = yen(row.get("personal_sales"))
            org_sales_yen      = yen(row.get("org_sales"))
            personal_f_yen     = yen(row.get("personal_f"))
            org_f_yen          = yen(row.get("org_f"))
            gross_yen          = yen(row.get("gross_reward"))
            child_staff_yen    = yen(row.get("child_staff_deduction"))
            child_baito_yen    = yen(row.get("child_baito_deduction"))
            rent_yen           = yen(row.get("rent"))
            total_yen          = yen(row.get("total_salary"))

            try:
                rate_pct = float(row.get("applied_rate") or 0) * 100
            except Exception:
                rate_pct = 0.0

            st.markdown("""
            <style>
            .pay-cards { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
            .pay-card {
              background: rgba(20, 24, 33, 0.55);
              border: 1px solid rgba(255,255,255,0.08);
              border-radius: 18px;
              padding: 14px 14px 12px 14px;
              box-shadow: 0 10px 30px rgba(0,0,0,0.25);
            }
            .pay-card .label {
              font-size: 13px;
              opacity: 0.80;
              font-weight: 500;
              line-height: 1.3;
              white-space: normal;
            }
            .pay-card .value {
              margin-top: 4px;
              font-size: 16px;
              font-weight: 600;
              line-height: 1.2;
              white-space: normal;
            }
            .pay-card .sub {
              margin-top: 4px;
              font-size: 11px;
              opacity: 0.60;
              line-height: 1.3;
              white-space: normal;
            }
            .pay-summary {
              margin: 10px 0 14px 0;
              background: rgba(10, 14, 22, 0.55);
              border: 1px solid rgba(255,255,255,0.10);
              border-radius: 22px;
              padding: 18px 18px 14px 18px;
            }
            .pay-summary .label { font-size: 13px; opacity: 0.80; }
            .pay-summary .value { margin-top: 8px; font-size: 38px; font-weight: 700; letter-spacing: 0.5px; }
            .pay-summary .sub { margin-top: 10px; font-size: 12px; opacity: 0.65; }
            </style>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="pay-summary">
              <div class="label">総支給額</div>
              <div class="value">¥{total_yen:,}</div>
              <div class="sub">F: {org_f_yen:,} / Rate: {rate_pct:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="pay-cards">
              <div class="pay-card"><div class="label">個人売上金額</div><div class="value">¥{personal_sales_yen:,}</div><div class="sub">売上明細ベース</div></div>
              <div class="pay-card"><div class="label">個人売上F</div><div class="value">{personal_f_yen:,}</div><div class="sub">カテゴリFの積算</div></div>
              <div class="pay-card"><div class="label">組織売上金額</div><div class="value">¥{org_sales_yen:,}</div><div class="sub">子売上含む（按分）</div></div>

              <div class="pay-card"><div class="label">組織売上F</div><div class="value">{org_f_yen:,}</div><div class="sub">給与のベース</div></div>
              <div class="pay-card"><div class="label">適用レート</div><div class="value">{rate_pct:.1f}%</div><div class="sub">rate_rules</div></div>
              <div class="pay-card"><div class="label">報酬額（gross）</div><div class="value">¥{gross_yen:,}</div><div class="sub">組織F × rate</div></div>

              <div class="pay-card"><div class="label">子staff控除</div><div class="value">¥{child_staff_yen:,}</div><div class="sub">子の報酬分を控除</div></div>
              <div class="pay-card"><div class="label">子baito控除</div><div class="value">¥{child_baito_yen:,}</div><div class="sub">子バイト給与分</div></div>
              <div class="pay-card"><div class="label">家賃</div><div class="value">¥{rent_yen:,}</div><div class="sub">固定</div></div>
            </div>
            """, unsafe_allow_html=True)

            # =========================
            # 給与確定・取消（スタッフ）
            # =========================
            st.markdown("### 給与確定・取消（スタッフ）")

            staff_info = fetch_df("""
            select
              staff_id, type, payment_method, stock_amount,
              bank_code, branch_code, bank_account_type, bank_account_number, bank_account_holder
            from public.staff
            where staff_id = :sid
            """, {"sid": staff_id})

            if staff_info.empty:
                st.error("staff テーブルに該当 staff_id が見つかりません。")
            else:
                staff_info = staff_info.iloc[0].to_dict()
                payment_method = staff_info.get("payment_method") or "cash"

                total_salary = yen(row.get("total_salary"))

                breakdown = {
                    "target_month": target_month_date.isoformat(),
                    "staff_id": staff_id,
                    "staff_type": "staff",
                    "inputs": {
                        "personal_sales": float(row.get("personal_sales") or 0),
                        "org_sales": float(row.get("org_sales") or 0),
                        "personal_f": float(row.get("personal_f") or 0),
                        "org_f": float(row.get("org_f") or 0),
                        "rate": float(row.get("applied_rate") or 0),
                        "child_staff_deduction": float(row.get("child_staff_deduction") or 0),
                        "child_baito_deduction": float(row.get("child_baito_deduction") or 0),
                        "rent": float(row.get("rent") or 0),
                    },
                    "calc": {
                        "gross_reward": float(row.get("gross_reward") or 0),
                        "total_salary": float(row.get("total_salary") or 0),
                    },
                    "meta": {
                        "rule_version": "F-diff-v1",
                        "calculated_at": datetime.now().isoformat(timespec="seconds"),
                        "payment_method": payment_method,
                    }
                }

                colA, colB = st.columns(2)

                with colA:
                    if st.button("給与確定（スタッフ）", disabled=is_confirmed, key="confirm_staff"):
                        # DB確定
                        exec_sql("""
                        insert into public.salary_confirms
                        (target_month, staff_id, staff_type, total_amount, breakdown, confirmed_at)
                        values
                        (:tm, :sid, :stype, :total, CAST(:breakdown AS jsonb), now())
                        """, {
                            "tm": target_month_date,
                            "sid": staff_id,
                            "stype": "staff",
                            "total": total_salary,
                            "breakdown": json.dumps(breakdown, ensure_ascii=False),
                        })

                        if payment_method == "stock":
                            exec_sql("""
                            update public.staff
                            set stock_amount = coalesce(stock_amount,0) + :amt
                            where staff_id = :sid
                            """, {"amt": total_salary, "sid": staff_id})

                        # ===== PDF用の項目（あなた指定）=====
                        rate_pct = float(row.get("applied_rate") or 0) * 100

                        left_items = [
                            ("個人売上金額", yen(row.get("personal_sales"))),
                            ("個人売上F", yen(row.get("personal_f"))),
                            ("組織売上金額", yen(row.get("org_sales"))),
                            ("組織売上F", yen(row.get("org_f"))),
                            ("適用レート", f"{rate_pct:.1f}%"),   # ★右側に%表示（0円にしない）
                            # ("報酬額", ...) は ★削除
                        ]

                        right_items = [
                            ("子staff控除", yen(row.get("child_staff_deduction"))),
                            ("子baito控除", yen(row.get("child_baito_deduction"))),
                            ("家賃", yen(row.get("rent"))),
                        ]

                        gross_reward = yen(row.get("gross_reward"))

                        pdf_bytes = build_payslip_pdf_like_template(
                            company_name="株式会社ＪＯＹ　ａｔ",
                            target_month_ym=target_month_ym,
                            staff_no=str(staff_id),
                            name=row["name"],
                            staff_type="staff",
                            net_amount=yen(row.get("total_salary")),
                            left_items=left_items,
                            right_items=right_items,
                            left_footer_amount=gross_reward,   # ★支給総額＝報酬額
                        )

                        st.session_state["payslip_pdf"] = pdf_bytes
                        st.session_state["payslip_filename"] = f"給与明細_{target_month_ym}_{row['name']}_staff.pdf"

                        st.success("給与確定しました（スタッフ）")
                        st.rerun()
                    # if st.session_state.get("payslip_pdf"):
                    #     st.download_button(
                    #         "📄給与明細PDF",
                    #         data=st.session_state["payslip_pdf"],
                    #         file_name=st.session_state.get("payslip_filename") or "給与明細.pdf",
                    #         mime="application/pdf",
                    #         use_container_width=True,
                    #     )
                        # 1回出したら消す（欲しければ消さなくてもOK）
                        # st.session_state["payslip_pdf"] = None
                        # st.session_state["payslip_filename"] = None

                with colB:
                    if st.button("給与取消（スタッフ）", disabled=not is_confirmed, key="cancel_staff"):
                        has_is_canceled = table_has_column("salary_confirms", "is_canceled")

                        if has_is_canceled:
                            exec_sql("""
                            update public.salary_confirms
                            set is_canceled = true, canceled_at = now()
                            where staff_id = :sid and staff_type='staff' and target_month = :tm
                            """, {"sid": staff_id, "tm": target_month_date})
                        else:
                            exec_sql("""
                            delete from public.salary_confirms
                            where staff_id = :sid and staff_type='staff' and target_month = :tm
                            """, {"sid": staff_id, "tm": target_month_date})

                        if payment_method == "stock":
                            exec_sql("""
                            update public.staff
                            set stock_amount = coalesce(stock_amount,0) - :amt
                            where staff_id = :sid
                            """, {"amt": total_salary, "sid": staff_id})

                        st.warning("給与取消しました（スタッフ）")
                        st.rerun()
with tab_confirms:
    st.subheader("✅ 確定情報（対象月）")

    has_is_canceled = table_has_column("salary_confirms", "is_canceled")

    # =========================================================
    # 1) 対象月の「対象者」一覧を作る（staff + baito）
    #    - staff: v_staff_net_salary の対象月に出てくる人
    #    - baito: v_baito_salary の対象月に出てくる人
    # =========================================================
    expected_staff = fetch_df("""
    select staff_id::text as staff_id, 'staff'::text as staff_type, name
    from public.v_staff_net_salary
    where target_month = :m
    """, {"m": target_month_date})

    expected_baito = fetch_df("""
    select staff_id::text as staff_id, 'baito'::text as staff_type, name
    from public.v_baito_salary
    where target_month = :m
    """, {"m": target_month_date})

    expected = pd.concat([expected_staff, expected_baito], ignore_index=True)

    if expected.empty:
        st.info("この対象月に給与対象者がいません（v_staff_net_salary / v_baito_salary が空）。")
        st.stop()

    # 念のため
    expected["staff_id"] = expected["staff_id"].astype(str)
    expected["staff_type"] = expected["staff_type"].astype(str)

    # =========================================================
    # 2) 対象月の確定レコード（最新の1件だけ）を staff_id+type 単位で取る
    # =========================================================
    confirms = fetch_df("""
    select
      staff_id::text as staff_id,
      staff_type,
      target_month,
      total_amount,
      breakdown,
      confirmed_at
      {extra_cols}
    from public.salary_confirms
    where target_month = :m
    """.format(extra_cols=(", is_canceled" if has_is_canceled else "")), {"m": target_month_date})

    if not confirms.empty:
        confirms["staff_id"] = confirms["staff_id"].astype(str)
        confirms["staff_type"] = confirms["staff_type"].astype(str)
        confirms["confirmed_at"] = pd.to_datetime(confirms["confirmed_at"], errors="coerce")

        # staff_id+type ごとに confirmed_at の最新を残す
        confirms = confirms.sort_values("confirmed_at", ascending=False)\
                           .drop_duplicates(subset=["staff_id", "staff_type"], keep="first")

    # =========================================================
    # 3) expected に confirms を left join して「未確定」も含めた一覧を作る
    # =========================================================
    view = expected.merge(
        confirms,
        on=["staff_id", "staff_type"],
        how="left",
        suffixes=("", "_c")
    )

    # 状態
    def compute_status(r):
        if pd.isna(r.get("confirmed_at")):
            return "未確定"
        if has_is_canceled and ("is_canceled" in r) and bool(r.get("is_canceled")):
            return "取消"
        return "確定"

    view["状態"] = view.apply(compute_status, axis=1)
    view["区分"] = view["staff_type"].map({"staff": "スタッフ", "baito": "バイト"}).fillna(view["staff_type"])
    view["確定金額"] = pd.to_numeric(view.get("total_amount"), errors="coerce").fillna(0).astype(int)
    view["確定日時"] = pd.to_datetime(view.get("confirmed_at"), errors="coerce")

    # =========================================================
    # 4) フィルタUI（状態に「未確定」追加）
    # =========================================================
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        kind = st.selectbox("区分", ["全て", "スタッフ", "バイト"], index=0, key="tab3_kind")
    with c2:
        state = st.selectbox("状態", ["全て", "未確定", "確定", "取消"], index=0, key="tab3_state")
    with c3:
        kw = st.text_input("検索（氏名/ID）", value="", key="tab3_kw")

    filtered = view.copy()
    if kind != "全て":
        filtered = filtered[filtered["区分"] == kind]
    if state != "全て":
        filtered = filtered[filtered["状態"] == state]
    if kw.strip():
        k = kw.strip().lower()
        filtered = filtered[
            filtered["name"].astype(str).str.lower().str.contains(k)
            | filtered["staff_id"].astype(str).str.lower().str.contains(k)
        ]

    # ソート（未確定→確定→取消 を上に、金額降順）
    status_order = {"未確定": 0, "確定": 1, "取消": 2}
    filtered["_o"] = filtered["状態"].map(status_order).fillna(9)
    filtered = filtered.sort_values(["_o", "確定金額", "name"], ascending=[True, False, True]).drop(columns=["_o"])

    # サマリー
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("件数", f"{len(filtered)}")
    with s2:
        st.metric("未確定", f"{int((filtered['状態']=='未確定').sum())}")
    with s3:
        st.metric("確定", f"{int((filtered['状態']=='確定').sum())}")
    with s4:
        st.metric("合計（確定分）", f"¥{int(filtered[filtered['状態']=='確定']['確定金額'].sum()):,}")

    st.markdown("---")

    # =========================================================
    # 5) 行ごとに描画（📄再発行 / 取消）
    # =========================================================
    # ヘッダー行
    h = st.columns([1.2, 1.2, 2.2, 1.4, 2.0, 1.2, 1.2])
    h[0].markdown("**状態**")
    h[1].markdown("**区分**")
    h[2].markdown("**氏名（ID）**")
    h[3].markdown("**確定金額**")
    h[4].markdown("**確定日時**")
    h[5].markdown("**📄再発行**")
    h[6].markdown("**取消**")

    def parse_breakdown(b):
        if b is None or (isinstance(b, float) and pd.isna(b)):
            return {}
        if isinstance(b, dict):
            return b
        if isinstance(b, str):
            try:
                return json.loads(b)
            except Exception:
                return {}
        return {}

    def build_pdf_from_breakdown(staff_type: str, staff_id: str, name: str, total_amount: int, breakdown: dict) -> bytes:
        # breakdown から items を復元
        left_items = []
        right_items = []
        left_footer_amount = None

        if staff_type == "staff":
            inp = (breakdown or {}).get("inputs", {})
            calc = (breakdown or {}).get("calc", {})
            rate_pct = float(inp.get("rate", 0) or 0) * 100

            left_items = [
                ("個人売上金額", inp.get("personal_sales", 0)),
                ("個人売上F", inp.get("personal_f", 0)),
                ("組織売上金額", inp.get("org_sales", 0)),
                ("組織売上F", inp.get("org_f", 0)),
                ("適用レート", f"{rate_pct:.1f}%"),
            ]
            right_items = [
                ("子staff控除", inp.get("child_staff_deduction", 0)),
                ("子baito控除", inp.get("child_baito_deduction", 0)),
                ("家賃", inp.get("rent", 0)),
            ]
            # ★支給総額＝報酬額（gross）
            left_footer_amount = (calc or {}).get("gross_reward", 0)

        else:
            inp = (breakdown or {}).get("inputs", {})
            calc = (breakdown or {}).get("calc", {})
            left_items = [
                ("時給計", (calc or {}).get("hourly_salary", 0)),
                ("交通費計", (calc or {}).get("transport_total", 0)),
                ("ドリンクバック", inp.get("drinkback_total", 0)),
            ]
            right_items = []
            left_footer_amount = None

        return build_payslip_pdf_like_template(
            company_name="株式会社ＪＯＹ　ａｔ",
            target_month_ym=target_month_ym,
            staff_no=staff_id,
            name=name,
            staff_type=staff_type,
            net_amount=total_amount,                 # 確定金額を差引支給額に
            left_items=left_items,
            right_items=right_items,
            left_footer_amount=left_footer_amount,   # staffは報酬額
        )

    # 行描画
    for idx, r in filtered.iterrows():
        status = r["状態"]
        stype = r["staff_type"]          # "staff"/"baito"
        kind_jp = r["区分"]
        sid = str(r["staff_id"])
        nm = str(r["name"])
        amt = int(r["確定金額"])
        dt = r["確定日時"]
        dt_str = "" if pd.isna(dt) else dt.strftime("%Y-%m-%d %H:%M:%S")

        cols = st.columns([1.2, 1.2, 2.2, 1.4, 2.0, 1.2, 1.2])
        cols[0].write(status)
        cols[1].write(kind_jp)
        cols[2].write(f"{nm}（{sid}）")
        cols[3].write(f"¥{amt:,}" if status != "未確定" else "-")
        cols[4].write(dt_str if status != "未確定" else "-")

        # 📄再発行：確定のみ（取消は出さない）
        if status == "確定":
            bd = parse_breakdown(r.get("breakdown"))
            pdf_bytes = build_pdf_from_breakdown(stype, sid, nm, amt, bd)

            cols[5].download_button(
                "📄",
                data=pdf_bytes,
                file_name=f"給与明細_{target_month_ym}_{nm}_{stype}_reissue.pdf",
                mime="application/pdf",
                key=f"reissue_{target_month_ym}_{stype}_{sid}",
                use_container_width=True
            )
        else:
            cols[5].write("")

        # 取消：確定のみ押せる（未確定/取消は無効）
        if status == "確定":
            if cols[6].button("取消", key=f"cancel_{target_month_ym}_{stype}_{sid}", use_container_width=True):
                if has_is_canceled:
                    exec_sql("""
                    update public.salary_confirms
                    set is_canceled = true, canceled_at = now()
                    where staff_id = :sid and staff_type = :st and target_month = :tm
                    """, {"sid": sid, "st": stype, "tm": target_month_date})
                else:
                    exec_sql("""
                    delete from public.salary_confirms
                    where staff_id = :sid and staff_type = :st and target_month = :tm
                    """, {"sid": sid, "st": stype, "tm": target_month_date})

                st.success("取消しました")
                st.rerun()
        else:
            cols[6].write("")