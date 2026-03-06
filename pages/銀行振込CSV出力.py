# pages/銀行振込CSV出力.py
import io
import re
import unicodedata
from datetime import date

import pandas as pd
import streamlit as st

from db import fetch_all  # ← 既存の db.py を利用

# 共通UI（既存プロジェクトに合わせる）
try:
    from ui.ui_style import apply_global_style
except Exception:
    apply_global_style = None

try:
    from ui.sidebar import render_sidebar
except Exception:
    render_sidebar = None
if not st.session_state.get("authenticated", False):
    st.switch_page("app.py")

# =========================
# 正規化
# =========================
def zfill_digits(value, width: int) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    s = re.sub(r"\D", "", s)
    return s.zfill(width)[:width] if s else ""


def normalize_account_type(v) -> str:
    """
    預金種目：
      普通 -> 1
      当座 -> 2
      貯蓄 -> 4
    すでに 1/2/4 が入ってればそのまま
    """
    if v is None:
        return ""
    s = str(v).strip()
    if s in {"1", "2", "4"}:
        return s
    if "普通" in s:
        return "1"
    if "当座" in s:
        return "2"
    if "貯蓄" in s:
        return "4"
    digits = re.sub(r"\D", "", s)
    return digits[:1] if digits else ""


def normalize_holder_kana(name: str) -> str:
    """
    口座名義は担当者マスタで半角カナ保存されている前提。
    ここでは全角化しない。
    """
    if name is None:
        return ""
    s = str(name).strip()
    s = s.replace("・", " ")
    s = s.replace("　", " ")
    s = re.sub(r"\s+", " ", s)
    return s[:48]


def yen_int(v) -> int:
    try:
        return int(float(v))
    except Exception:
        return 0


# =========================
# DB 取得（db.py）
# =========================
def load_bank_targets(*args) -> pd.DataFrame:
    """
    互換用：旧呼び出し load_bank_targets(year, month) と
           新呼び出し load_bank_targets("YYYY-MM") の両方を受ける
    """
    if len(args) == 1:
        target_month = str(args[0]).strip()
    elif len(args) == 2:
        year = int(args[0])
        month = int(args[1])
        target_month = f"{year:04d}-{month:02d}"
    else:
        raise TypeError("load_bank_targets は (target_month) か (year, month) のどちらかで呼んでください。")

    sql = """
    SELECT
    sc.confirm_id,
    sc.target_month,
    sc.staff_id,
    sc.staff_type,
    sc.total_amount,
    sc.breakdown,
    sc.confirmed_at,

    s.name,
    s.type,
    s.payment_method,
    s.bank_name,
    s.bank_branch,
    s.bank_code,
    s.branch_code,
    s.bank_account_type,
    s.bank_account_number,
    s.bank_account_holder
    FROM salary_confirms sc
    JOIN staff s
    ON s.staff_id = sc.staff_id
    WHERE to_char(sc.target_month, 'YYYY-MM') = %(ym)s
    AND s.payment_method = 'bank'
    ORDER BY s.name
    """
    rows = fetch_all(sql, {"ym": target_month})
    return pd.DataFrame(rows)


# =========================
# CSV生成（GMO所定CSV）
# =========================
def build_gmo_csv(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["bank_code"] = df["bank_code"].apply(lambda x: zfill_digits(x, 4))
    out["branch_code"] = df["branch_code"].apply(lambda x: zfill_digits(x, 3))
    out["account_type"] = df["bank_account_type"].apply(normalize_account_type)
    out["account_number"] = df["bank_account_number"].apply(lambda x: zfill_digits(x, 7))
    out["holder_kana"] = df["bank_account_holder"].apply(normalize_holder_kana)
    out["amount"] = df["total_amount"].apply(yen_int)

    # 任意列（空欄でOK）
    out["edi"] = ""
    out["customer_code"] = ""
    out["requester_name"] = ""
    out["identifier"] = ""
    return out


def validate_row(r) -> str:
    errs = []
    if len(str(r["bank_code"])) != 4 or not str(r["bank_code"]).isdigit():
        errs.append("bank_code不正")
    if len(str(r["branch_code"])) != 3 or not str(r["branch_code"]).isdigit():
        errs.append("branch_code不正")
    if r["account_type"] not in {"1", "2", "4"}:
        errs.append("account_type不正(1/2/4)")
    if len(str(r["account_number"])) != 7 or not str(r["account_number"]).isdigit():
        errs.append("account_number不正")
    if not str(r["holder_kana"]).strip():
        errs.append("名義空")
    if yen_int(r["amount"]) <= 0:
        errs.append("金額<=0")
    return " / ".join(errs)


def to_shiftjis_bytes(df: pd.DataFrame) -> bytes:
    csv_str = df.to_csv(index=False, header=False, lineterminator="\r\n")
    return csv_str.encode("shift_jis", errors="replace")


# =========================
# UI
# =========================
st.set_page_config(page_title="銀行振込CSV出力", layout="wide")

if apply_global_style:
    apply_global_style()
if render_sidebar:
    render_sidebar()

st.title("🏦 銀行振込CSV出力")
st.caption("対象月の確定給与（salary_confirm）から、GMO総合振込アップロード用CSV（当社所定CSV）を生成します。")

today = date.today()
default_ym = f"{today.year:04d}-{today.month:02d}"
ym = st.text_input("対象月（YYYY-MM）", value=default_ym)

m = re.fullmatch(r"(\d{4})-(\d{2})", ym.strip())
if not m:
    st.error("対象月は YYYY-MM 形式で入力してください（例: 2026-03）")
    st.stop()

year = int(m.group(1))
month = int(m.group(2))
if not (1 <= month <= 12):
    st.error("月は 01〜12 の範囲で入力してください。")
    st.stop()

col1, col2 = st.columns([1, 1])
with col1:
    include_zero = st.checkbox("0円も出力する", value=False)
with col2:
    strict_validate = st.checkbox("不備があれば出力しない（厳格）", value=False)

with st.spinner("データ取得中..."):
    base_df = load_bank_targets(ym.strip())

if base_df.empty:
    st.warning("対象月の『銀行振込(payment_method=bank)』の確定データがありません。")
    st.stop()

base_df["total_amount"] = base_df["total_amount"].apply(yen_int)
if not include_zero:
    base_df = base_df[base_df["total_amount"] > 0].copy()

if base_df.empty:
    st.warning("出力対象が0件です（0円除外設定の影響など）。")
    st.stop()

st.subheader("プレビュー")
sum_amount = int(base_df["total_amount"].sum())
st.info(f"対象件数: {len(base_df)} 件 / 合計振込額: ¥{sum_amount:,}")

preview_cols = [
    "staff_id", "name", "total_amount",
    "bank_name", "bank_branch",
    "bank_code", "branch_code",
    "bank_account_type", "bank_account_number", "bank_account_holder",
]
st.dataframe(base_df[preview_cols], use_container_width=True, hide_index=True)

out_df = build_gmo_csv(base_df)
out_df["__errors"] = out_df.apply(validate_row, axis=1)
has_errors = (out_df["__errors"] != "").any()

if has_errors:
    st.error("CSV出力データに不備があります。下のエラー一覧を確認してください。")
    st.dataframe(out_df[out_df["__errors"] != ""], use_container_width=True, hide_index=True)
    if strict_validate:
        st.stop()

csv_bytes = to_shiftjis_bytes(out_df.drop(columns=["__errors"]))
filename = f"gmo_transfer_{year:04d}-{month:02d}.csv"

st.subheader("CSVダウンロード")
st.download_button(
    label="⬇️ GMO総合振込CSVをダウンロード（Shift-JIS）",
    data=csv_bytes,
    file_name=filename,
    mime="text/csv",
)

with st.expander("CSV先頭10行プレビュー（ヘッダ無し）"):
    st.code(out_df.drop(columns=["__errors"]).head(10).to_csv(index=False, header=False), language="csv")