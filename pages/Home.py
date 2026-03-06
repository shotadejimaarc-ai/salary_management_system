from ui.ui_style import apply_global_style
apply_global_style()

from ui.sidebar import render_sidebar
render_sidebar()

import streamlit as st
from pathlib import Path
from datetime import date
from db import fetch_one, fetch_all

st.set_page_config(page_title="給与管理システム", layout="wide")

from ui.loading import show_loading, clear_loading

loading_box, progress = show_loading("画面を読み込み中です...")

# ===== ロゴパス（Homeの場所が変わっても拾える）=====
HERE = Path(__file__).resolve()
CANDIDATES = [
    HERE.parent / "ui" / "logo.png",
    HERE.parent.parent / "ui" / "logo.png",
    HERE.parent.parent.parent / "ui" / "logo.png",
]
LOGO_PATH = next((p for p in CANDIDATES if p.exists()), None)

# ===== 月計算 =====
today = date.today()
this_month_first = date(today.year, today.month, 1)

if today.month == 1:
    last_month_year = today.year - 1
    last_month_month = 12
else:
    last_month_year = today.year
    last_month_month = today.month - 1

if last_month_month == 1:
    prev_month_year = last_month_year - 1
    prev_month_month = 12
else:
    prev_month_year = last_month_year
    prev_month_month = last_month_month - 1

last_month_ym = f"{last_month_year:04d}-{last_month_month:02d}"
prev_month_ym = f"{prev_month_year:04d}-{prev_month_month:02d}"

# ===== 集計取得 =====

def safe_int(v, default=0):
    try:
        if v is None:
            return default
        return int(float(v))
    except Exception:
        return default

def get_confirm_status(target_month: str):
    # staffテーブル上の人数
    staff_total_row = fetch_one("""
        SELECT COUNT(*) AS cnt
        FROM public.staff
        WHERE type = 'staff'
    """)
    baito_total_row = fetch_one("""
        SELECT COUNT(*) AS cnt
        FROM public.staff
        WHERE type = 'baito'
    """)

    # salary_confirms上の確定人数
    staff_confirmed_row = fetch_one("""
        SELECT COUNT(DISTINCT staff_id) AS cnt
        FROM public.salary_confirms
        WHERE target_month = to_date(%(ym)s || '-01', 'YYYY-MM-DD')
          AND staff_type = 'staff'
    """, {"ym": target_month})

    baito_confirmed_row = fetch_one("""
        SELECT COUNT(DISTINCT staff_id) AS cnt
        FROM public.salary_confirms
        WHERE target_month = to_date(%(ym)s || '-01', 'YYYY-MM-DD')
          AND staff_type = 'baito'
    """, {"ym": target_month})

    return {
        "staff_total": safe_int((staff_total_row or {}).get("cnt")),
        "baito_total": safe_int((baito_total_row or {}).get("cnt")),
        "staff_confirmed": safe_int((staff_confirmed_row or {}).get("cnt")),
        "baito_confirmed": safe_int((baito_confirmed_row or {}).get("cnt")),
    }

def get_last_confirmed_at():
    row = fetch_one("""
        SELECT MAX(confirmed_at) AS last_confirmed_at
        FROM public.salary_confirms
    """)
    return (row or {}).get("last_confirmed_at")
progress.progress(20)
def get_sales_total(target_month: str):
    # payments.paid_at から月次売上を集計
    progress.progress(40)
    row = fetch_one("""
        SELECT COALESCE(SUM(total_amount), 0) AS total
        FROM public.payments
        WHERE to_char(paid_at AT TIME ZONE 'Asia/Tokyo', 'YYYY-MM') = %(ym)s
    """, {"ym": target_month})
    return safe_int((row or {}).get("total"))

progress.progress(60)
confirm_status = get_confirm_status(last_month_ym)
last_confirmed_at = get_last_confirmed_at()

sales_last = get_sales_total(last_month_ym)
sales_prev = get_sales_total(prev_month_ym)

progress.progress(80)
if sales_prev > 0:
    sales_diff_pct = ((sales_last - sales_prev) / sales_prev) * 100
    sales_diff_text = f"{sales_diff_pct:+.1f}%"
else:
    sales_diff_text = "—"


progress.progress(100)
clear_loading(loading_box, progress)

# ===== 高級バーUI（フォント＋背景＋タイポ＋カード）=====
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;700;900&family=Shippori+Mincho:wght@500;700&display=swap" rel="stylesheet">
    <style>
        .main{
        background:
            radial-gradient(900px 420px at 50% 30%, rgba(255,215,120,0.10), transparent 60%),
            radial-gradient(800px 360px at 55% 55%, rgba(60,255,122,0.06), transparent 55%),
            linear-gradient(180deg, #0A0F18 0%, #070A10 65%, #05070C 100%);
        }

        .hero-logo{
        width: 360px;
        max-width: 78vw;
        border-radius: 22px;
        box-shadow: 0 18px 60px rgba(0,0,0,0.55);
        filter: saturate(1.03) contrast(1.03);
        margin-bottom: 18px;
        transform: translateX(36px);
        }

        .hero-title{
        font-family: 'Shippori Mincho', serif;
        font-size: 3.0rem;
        font-weight: 700;
        white-space: nowrap;
        letter-spacing: 0.18em;
        line-height: 1.05;
        margin: 0;
        color: rgba(255,255,255,0.92);
        text-shadow: 0 0 28px rgba(255,215,120,0.14);
        }

        .hero-line{
        width: 360px;
        max-width: 82vw;
        height: 2px;
        background: linear-gradient(90deg,
            rgba(255,215,120,0.00),
            rgba(255,215,120,0.55),
            rgba(255,215,120,0.00)
        );
        margin: 16px auto 8px auto;
        }

        .hero-badge{
        margin-top: 14px;
        font-family: 'Montserrat', sans-serif;
        font-size: 0.85rem;
        letter-spacing: 0.22em;
        color: rgba(255,215,120,0.85);
        padding: 0.45rem 0.85rem;
        border-radius: 999px;
        border: 1px solid rgba(255,215,120,0.28);
        background: rgba(255,215,120,0.06);
        }

        .dashboard-wrap{
        margin-top: 34px;
        }

        .dash-card{
        height:100%;
        width:100%;
        background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.025));
        border: 1px solid rgba(255,215,120,0.12);
        border-radius: 22px;
        padding: 22px 24px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.28);
        backdrop-filter: blur(8px);
        min-height: 150px;
        }

        .dash-label{
        font-family: 'Montserrat', sans-serif;
        font-size: 0.82rem;
        letter-spacing: 0.16em;
        color: rgba(255,215,120,0.78);
        margin-bottom: 14px;
        }

        .dash-value{
        font-family: 'Montserrat', sans-serif;
        font-size: 1.5rem;
        font-weight: 500;
        color: rgba(255,255,255,0.94);
        line-height: 1.15;
        }

        .dash-sub{
        margin-top: 10px;
        font-size: 0.98rem;
        color: rgba(255,255,255,0.72);
        line-height: 1.7;
        }

        .dash-strong{
        color: rgba(255,255,255,0.96);
        font-weight: 700;
        }

        .dash-muted{
        color: rgba(255,255,255,0.58);
        }

        @media (max-width: 680px){
        .hero-title{ font-size: 2.5rem; letter-spacing: 0.12em; }
        .hero-logo{ width: 280px; }
        .hero-line{ width: 260px; }
        .dash-value{ font-size: 1.6rem; }
        }
    </style>
""",
    unsafe_allow_html=True
)

# ===== 中央固定（columnsでズレ防止）=====
l, c, r = st.columns([1, 2, 1])
with c:
    if LOGO_PATH:
        st.markdown(
            f'<img src="data:image/png;base64,{LOGO_PATH.read_bytes().hex()}" style="display:none;">',
            unsafe_allow_html=True
        )

    if LOGO_PATH:
        import base64
        b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")
        st.markdown(
            f'<img class="hero-logo" src="data:image/png;base64,{b64}" />',
            unsafe_allow_html=True
        )
    else:
        st.caption("※ ui/logo.png が見つかりません（パス確認して）")

    st.markdown('<div class="hero-title">給与管理システム</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-line"></div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-badge">　　　　SALARY MANAGEMENT SYSTEM</div>', unsafe_allow_html=True)



# ===== ダッシュボード =====
st.markdown('<div class="dashboard-wrap">', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="dash-card">
        <div class="dash-label">PAYROLL STATUS</div>
        <div class="dash-value">給与確定状況</div>
        <div class="dash-sub">
            スタッフ　
            <span class="dash-strong">{confirm_status['staff_confirmed']}</span>
            <span class="dash-muted">/ {confirm_status['staff_total']}</span>
            <br>
            バイト　　
            <span class="dash-strong">{confirm_status['baito_confirmed']}</span>
            <span class="dash-muted">/ {confirm_status['baito_total']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    last_confirm_text = "未確定"
    if last_confirmed_at:
        try:
            last_confirm_text = last_confirmed_at.strftime("%Y-%m-%d %H:%M")
        except Exception:
            last_confirm_text = str(last_confirmed_at)

    st.markdown(f"""
    <div class="dash-card">
        <div class="dash-label">LAST CONFIRMED</div>
        <div class="dash-value">{last_confirm_text}</div>
        <div class="dash-sub">
            給与確定を実行した日時
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="dash-card">
        <div class="dash-label">SALES ({last_month_ym})</div>
        <div class="dash-value">¥{sales_last:,}</div>
        <div class="dash-sub">
            先月売上
        </div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="dash-card">
        <div class="dash-label">M OVER M</div>
        <div class="dash-value">{sales_diff_text}</div>
        <div class="dash-sub">
            前月（{prev_month_ym}）比
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)