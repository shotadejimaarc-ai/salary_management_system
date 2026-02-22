import streamlit as st
from datetime import datetime
import pandas as pd
from repositories.staff_repository import StaffRepository
from repositories.salary_repository import SalaryRepository

from ui.ui_style import apply_global_style
apply_global_style()

st.title("🏦 振込データ出力")

# ==============================
# 月選択
# ==============================
col1, col2 = st.columns(2)
with col1:
    year = st.number_input("年", value=datetime.now().year)
with col2:
    month = st.number_input("月", value=datetime.now().month)

st.divider()

# ==============================
# 確定給与取得
# ==============================
salary_rows = SalaryRepository.get_confirmed_salaries(year, month)

if not salary_rows:
    st.warning("この月の確定済み給与はありません")
    st.stop()

# salary_rows想定構造：
# (id, staff_id, year, month, amount, confirmed_at)

# ==============================
# スタッフ取得
# ==============================
staff_list = StaffRepository.load_all()
staff_map = {s.id: s for s in staff_list}

# ==============================
# 確定済みスタッフのみ抽出
# ==============================
confirmed_staff_ids = [row[1] for row in salary_rows]

transfer_candidates = [
    staff_map[sid]
    for sid in confirmed_staff_ids
    if sid in staff_map
]

if not transfer_candidates:
    st.warning("振込可能なスタッフがいません")
    st.stop()

# ==============================
# スタッフ選択
# ==============================
staff_dict = {s.id: s for s in transfer_candidates}

selected_ids = st.multiselect(
    "振込対象スタッフを選択",
    options=list(staff_dict.keys()),
    format_func=lambda x: staff_dict[x].name
)

st.divider()

# ==============================
# プレビュー
# ==============================
if selected_ids:

    preview_rows = []
    total_transfer = 0

    for row in salary_rows:
        staff_id = row[1]
        amount = row[4]

        if staff_id not in selected_ids:
            continue

        staff = staff_map.get(staff_id)

        # 口座未登録チェック
        if not staff.bank_code or not staff.branch_code or not staff.account_number:
            st.error(f"{staff.name} の銀行情報が未登録です")
            st.stop()

        total_transfer += amount

        preview_rows.append({
            "氏名": staff.name,
            "銀行コード": staff.bank_code,
            "支店コード": staff.branch_code,
            "口座種別": staff.account_type,
            "口座番号": staff.account_number,
            "金額": amount
        })

    df_preview = pd.DataFrame(preview_rows)

    st.markdown("### 💰 振込内容プレビュー")
    st.dataframe(df_preview, use_container_width=True)

    st.metric("振込総額", f"¥{total_transfer:,}")

    st.divider()

    # ==============================
    # CSV生成
    # ==============================
    if st.button("📤 振込CSVを生成", use_container_width=True):

        df_export = df_preview.copy()

        csv_data = df_export.to_csv(
            index=False,
            encoding="cp932"   # 日本銀行必須
        )

        file_name = f"salary_transfer_{year}_{month}.csv"

        st.download_button(
            label="📥 CSVダウンロード",
            data=csv_data,
            file_name=file_name,
            mime="text/csv",
            use_container_width=True
        )

    # ==============================
    # ロック処理
    # ==============================
    if st.button("🔒 この月をロックする", use_container_width=True):
        SalaryRepository.lock_salary(year, month)
        st.success("この月はロックされました")
        st.rerun()

else:
    st.info("振込対象スタッフを選択してください")