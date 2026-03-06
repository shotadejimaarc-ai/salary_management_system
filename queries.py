import pandas as pd
from db import get_conn
import json
import pandas as pd
from db import get_conn
from datetime import datetime
from psycopg2.extras import execute_values
import requests
import time


def q_baito_staff():
    with get_conn() as conn:
        return pd.read_sql(
            """
            select staff_id, name, hourly_wage, transportation_allowance
            from staff
            where type = 'baito'
            order by name
            """,
            conn,
        )

def q_drinkback_monthly(year_month: str):
    # v_drinkback_monthly:
    # target_month (date), staff_id, staff_name, drinkback_total
    with get_conn() as conn:
        return pd.read_sql(
            """
            select staff_id, drinkback_total
            from v_drinkback_monthly
            where to_char(target_month, 'YYYY-MM') = %s
            """,
            conn,
            params=[year_month],
        )

def q_staff_monthly_hours(year_month: str):
    # v_staff_monthly_hours がまだ無い想定：あっても動く
    with get_conn() as conn:
        return pd.read_sql(
            """
            select staff_id, total_hours
            from v_staff_monthly_hours
            where to_char(work_month, 'YYYY-MM') = %s
            """,
            conn,
            params=[year_month],
        )

def q_drinkback_items(year_month: str, staff_id: str):
    with get_conn() as conn:
        return pd.read_sql(
            """
            select *
            from v_drinkback_items
            where credit_staff_id = %s
              and to_char(business_date, 'YYYY-MM') = %s
            order by business_date asc, created_at asc
            """,
            conn,
            params=[staff_id, year_month],
        )

# def q_staff_master_all():
#     with get_conn() as conn:
#         return pd.read_sql(
#             """
#             select staff_id, name, type, parent_id, hourly_wage, transportation_allowance
#             from staff
#             order by staff_id
#             """,
#             conn,
#         )

def q_gross_reward_month(year_month: str):
    with get_conn() as conn:
        return pd.read_sql(
            """
            select staff_id, target_month, org_sales, rate, gross_reward
            from v_staff_gross_reward
            where to_char(target_month, 'YYYY-MM') = %s
            """,
            conn,
            params=[year_month],
        )


def fetch_df(sql: str, params=None) -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql(sql, conn, params=params)

def exec_sql(sql: str, params=None):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, params or [])
        conn.commit()

# --- 参照系 ---
def q_categories():
    return fetch_df("""
        select category_id, name, f_rate, is_drink_back
        from category
        order by category_id
    """)

def q_staff_master_all():
    return fetch_df("""
        select
          staff_id, name, type, parent_id, parent_id_2,
          hourly_wage, transportation_allowance,
          bank_code,branch_code,
          bank_name, bank_branch, bank_account_type, bank_account_number, bank_account_holder,
          payment_method
        from staff
        order by staff_id
    """)

def q_rate_rules():
    return fetch_df("""
        select rule_id, min_amount, max_amount, rate, is_active, sort_order
        from rate_rules
        order by sort_order, min_amount
    """)

def q_gross_reward_month(year_month: str):
    return fetch_df("""
        select staff_id, target_month, org_sales, rate, gross_reward
        from v_staff_gross_reward
        where to_char(target_month,'YYYY-MM')=%s
    """, [year_month])

def q_personal_sales_month(year_month: str):
    return fetch_df("""
        select staff_id, personal_sales
        from v_staff_personal_sales_monthly
        where to_char(target_month,'YYYY-MM')=%s
        order by staff_id
    """, [year_month])

def q_drinkback_monthly(year_month: str):
    return fetch_df("""
        select staff_id, drinkback_total
        from v_drinkback_monthly
        where to_char(target_month,'YYYY-MM')=%s
    """, [year_month])

def q_staff_monthly_hours(year_month: str):
    return fetch_df("""
        select staff_id, total_hours
        from v_staff_monthly_hours
        where to_char(work_month,'YYYY-MM')=%s
    """, [year_month])

def q_monthly_diff(year_month: str):
    return fetch_df("""
        select *
        from v_monthly_payment_vs_items_diff
        where to_char(target_month,'YYYY-MM')=%s
    """, [year_month])

# --- 更新系 ---
def upsert_rate_rule(rule_id, min_amount, max_amount, rate, is_active, sort_order):
    exec_sql("""
        insert into rate_rules (rule_id, min_amount, max_amount, rate, is_active, sort_order)
        values (%s,%s,%s,%s,%s,%s)
        on conflict (rule_id)
        do update set min_amount=excluded.min_amount,
                     max_amount=excluded.max_amount,
                     rate=excluded.rate,
                     is_active=excluded.is_active,
                     sort_order=excluded.sort_order
    """, [rule_id, min_amount, max_amount, rate, is_active, sort_order])

def update_category(category_id, f_rate, is_drink_back):
    exec_sql("""
        update category
        set f_rate=%s, is_drink_back=%s
        where category_id=%s
    """, [f_rate, is_drink_back, category_id])

def update_staff_master(row: dict):
    sql = """
        update staff
        set
            type=%s,
            parent_id=%s,
            parent_id_2=%s,
            bank_code=%s,
            branch_code=%s,
            bank_name=%s,
            bank_branch=%s,
            bank_account_type=%s,
            bank_account_number=%s,
            bank_account_holder=%s,
            payment_method=%s
        where staff_id=%s
    """

    params = [
        row.get("type"),
        row.get("parent_id"),
        row.get("parent_id_2"),
        row.get("bank_code"),
        row.get("branch_code"),
        row.get("bank_name"),
        row.get("bank_branch"),
        row.get("bank_account_type"),
        row.get("bank_account_number"),
        row.get("bank_account_holder"),
        row.get("payment_method"),
        row.get("staff_id"),
    ]

    exec_sql(sql, params)

def upsert_salary_confirm(target_month_date, staff_id, staff_type, total_amount, breakdown: dict):
    exec_sql("""
        insert into salary_confirms (target_month, staff_id, staff_type, total_amount, breakdown)
        values (%s,%s,%s,%s,%s::jsonb)
        on conflict (target_month, staff_id)
        do update set staff_type=excluded.staff_type,
                     total_amount=excluded.total_amount,
                     breakdown=excluded.breakdown,
                     confirmed_at=now()
    """, [target_month_date, staff_id, staff_type, int(total_amount), json.dumps(breakdown, ensure_ascii=False)])

def add_stock_amount(staff_id: str, delta: int):
    exec_sql("""
        update staff
        set stock_amount = coalesce(stock_amount,0) + %s
        where staff_id = %s
    """, [int(delta), staff_id])

def q_baito_shift_month(year_month: str):
    return fetch_df("""
        select target_month, staff_id, hourly_wage, total_hours, transport_one_way, attendance_days
        from baito_shift_monthly
        where to_char(target_month,'YYYY-MM')=%s
        order by staff_id
    """, [year_month])

def upsert_baito_shift_month(target_month_date, staff_id, hourly_wage, total_hours, transport_one_way, attendance_days):
    exec_sql("""
        insert into baito_shift_monthly
          (target_month, staff_id, hourly_wage, total_hours, transport_one_way, attendance_days, updated_at)
        values
          (%s,%s,%s,%s,%s,%s, now())
        on conflict (target_month, staff_id)
        do update set
          hourly_wage=excluded.hourly_wage,
          total_hours=excluded.total_hours,
          transport_one_way=excluded.transport_one_way,
          attendance_days=excluded.attendance_days,
          updated_at=now()
    """, [target_month_date, staff_id, int(hourly_wage), float(total_hours), int(transport_one_way), int(attendance_days)])

def q_bank_branch_list(keyword: str = ""):
    kw = (keyword or "").strip()
    if kw == "":
        return fetch_df("""
            select
              b.bank_code, b.bank_name,
              br.branch_code, br.branch_name
            from banks b
            join bank_branches br
              on b.bank_code = br.bank_code
            order by b.bank_code, br.branch_code
            limit 2000
        """)
    return fetch_df("""
        select
          b.bank_code, b.bank_name,
          br.branch_code, br.branch_name
        from banks b
        join bank_branches br
          on b.bank_code = br.bank_code
        where
          b.bank_code ilike %s
          or b.bank_name ilike %s
          or br.branch_code ilike %s
          or br.branch_name ilike %s
        order by b.bank_code, br.branch_code
        limit 2000
    """, [f"%{kw}%"] * 4)


def _fetch_all_banks_api():
    banks = []
    page = 1
    while True:
        url = f"https://bank.teraren.com/banks.json?page={page}"
        res = requests.get(url, timeout=30)
        if res.status_code != 200:
            break
        data = res.json()
        if not data:
            break
        banks.extend(data)
        page += 1
        time.sleep(0.15)
    return banks

def _fetch_branches_api(bank_code_4: str):
    branches = []
    page = 1
    while True:
        url = f"https://bank.teraren.com/banks/{bank_code_4}/branches.json?page={page}"
        res = requests.get(url, timeout=30)
        if res.status_code != 200:
            break
        data = res.json()
        if not data:
            break
        branches.extend(data)
        page += 1
        time.sleep(0.15)
    return branches

def refresh_bank_master_from_api(progress_cb=None):
    """
    progress_cb: (current:int, total:int, message:str) -> None みたいなコールバックを想定（Streamlitの進捗表示用）
    """
    banks = _fetch_all_banks_api()
    total = len(banks)

    now = datetime.now()

    bank_rows = []
    branch_rows = []

    for i, b in enumerate(banks, start=1):
        bank_code = str(b.get("code")).zfill(4)
        bank_name = b.get("name") or ""

        bank_rows.append((bank_code, bank_name, now, now))

        brs = _fetch_branches_api(bank_code)
        for br in brs:
            branch_code = str(br.get("code")).zfill(3)
            branch_name = br.get("name") or ""
            branch_rows.append((bank_code, branch_code, branch_name, now, now))

        if progress_cb:
            progress_cb(i, total, f"{bank_code} {bank_name}")

    with get_conn() as conn:
        cur = conn.cursor()
        try:
            cur.execute("begin")

            # 洗い替え
            cur.execute("truncate table bank_branches, banks")

            # banks insert
            execute_values(
                cur,
                "insert into banks (bank_code, bank_name, created_at, updated_at) values %s",
                bank_rows,
                page_size=1000
            )

            # branches insert
            execute_values(
                cur,
                "insert into bank_branches (bank_code, branch_code, branch_name, created_at, updated_at) values %s",
                branch_rows,
                page_size=5000
            )

            conn.commit()
            return {"banks": len(bank_rows), "branches": len(branch_rows)}

        except Exception:
            conn.rollback()
            raise

def q_banks(keyword: str = ""):
    kw = (keyword or "").strip()
    if kw == "":
        return fetch_df("""
            select bank_code, bank_name
            from banks
            order by bank_code
            limit 500
        """)
    return fetch_df("""
        select bank_code, bank_name
        from banks
        where bank_code ilike %s or bank_name ilike %s
        order by bank_code
        limit 500
    """, [f"%{kw}%", f"%{kw}%"])

def q_branches(bank_code: str, keyword: str = ""):
    if not bank_code:
        return fetch_df("""
            select bank_code, branch_code, branch_name
            from bank_branches
            where 1=0
        """)
    kw = (keyword or "").strip()
    if kw == "":
        return fetch_df("""
            select bank_code, branch_code, branch_name
            from bank_branches
            where bank_code = %s
            order by branch_code
            limit 2000
        """, [bank_code])
    return fetch_df("""
        select bank_code, branch_code, branch_name
        from bank_branches
        where bank_code = %s
          and (branch_code ilike %s or branch_name ilike %s)
        order by branch_code
        limit 2000
    """, [bank_code, f"%{kw}%", f"%{kw}%"])

def q_sales_total_month(year_month: str):
    return fetch_df("""
        select
          %s as target_month,
          coalesce(sum(p.total_amount), 0) as sales_total
        from payments p
        where to_char(p.business_date, 'YYYY-MM') = %s
    """, [year_month, year_month])


def q_staff_sales_detail_month(year_month: str, staff_id: str):
    return fetch_df("""
        select
          oi.business_date,
          oi.created_at,
          oi.order_id,
          m.name as menu_name,
          c.name as category_name,
          oi.qty,
          oi.unit_price,
          (oi.qty * oi.unit_price) as line_total,
          oi.is_paid
        from order_items oi
        join orders o on o.order_id = oi.order_id
        join menu m on m.menu_id = oi.menu_id
        left join category c on c.category_id = m.category_id
        where to_char(oi.business_date, 'YYYY-MM') = %s
          and oi.credit_staff_id = %s
        order by oi.created_at desc, oi.order_id desc
        limit 2000
    """, [year_month, staff_id])

def q_baito_mapping_detail_month(year_month: str):
    """
    バイトに帰属している売上明細のうち、
    ドリンクバック以外を『親staff』へマッピングすべき候補一覧を返す。
    月判定は business_date ベース。
    """
    return fetch_df("""
        select
          oi.business_date,
          oi.created_at,
          oi.item_id,
          oi.order_id,
          oi.menu_id,
          m.name as menu_name,
          c.name as category_name,
          coalesce(c.is_drink_back, false) as is_drink_back,
          oi.qty,
          oi.unit_price,
          (oi.qty * oi.unit_price) as line_total,

          oi.credit_staff_id as baito_staff_id,
          bs.name as baito_staff_name,
          bs.parent_id as mapped_staff_id,
          ps.name as mapped_staff_name,
          bs.parent_id_2 as sub_parent_id,

          case
            when coalesce(c.is_drink_back, false) = true then '対象外（ドリンクバック）'
            when bs.type <> 'baito' then '対象外（バイト以外）'
            when bs.parent_id is null or trim(bs.parent_id::text) = '' then '親未設定'
            when bs.parent_id_2 is not null and trim(bs.parent_id_2::text) <> '' then '親2あり（要確認）'
            else '親へマッピング'
          end as mapping_status
        from public.order_items oi
        join public.orders o
          on o.order_id = oi.order_id
        left join public.menu m
          on m.menu_id = oi.menu_id
        left join public.category c
          on c.category_id = m.category_id
        join public.staff bs
          on bs.staff_id::text = oi.credit_staff_id::text
        left join public.staff ps
          on ps.staff_id::text = bs.parent_id::text
        where oi.is_paid = true
          and to_char(oi.business_date, 'YYYY-MM') = %s
          and bs.type = 'baito'
        order by oi.business_date desc, oi.created_at desc, oi.order_id desc
    """, [year_month])

def q_baito_mapping_summary_month(year_month: str):
    """
    更新対象候補の件数・金額を親スタッフ別に集計
    """
    return fetch_df("""
        select
          bs.parent_id as mapped_staff_id,
          ps.name as mapped_staff_name,
          count(*) as item_count,
          coalesce(sum(oi.qty * oi.unit_price), 0) as total_amount
        from public.order_items oi
        left join public.menu m
          on m.menu_id = oi.menu_id
        left join public.category c
          on c.category_id = m.category_id
        join public.staff bs
          on bs.staff_id::text = oi.credit_staff_id::text
        left join public.staff ps
          on ps.staff_id::text = bs.parent_id::text
        where oi.is_paid = true
          and to_char(oi.business_date, 'YYYY-MM') = %s
          and bs.type = 'baito'
          and coalesce(c.is_drink_back, false) = false
          and bs.parent_id is not null
          and trim(bs.parent_id::text) <> ''
          and (bs.parent_id_2 is null or trim(bs.parent_id_2::text) = '')
        group by bs.parent_id, ps.name
        order by total_amount desc, item_count desc
    """, [year_month])


def exec_baito_mapping_update_month(year_month: str):
    """
    バイト帰属（非ドリンクバック）の売上明細を、親staffへ一括付替する
    戻り値: 更新件数
    """
    sql = """
        update public.order_items oi
        set credit_staff_id = bs.parent_id
        from public.menu m
        left join public.category c
          on c.category_id = m.category_id
        join public.staff bs
          on bs.staff_id::text = oi.credit_staff_id::text
        where m.menu_id = oi.menu_id
          and oi.is_paid = true
          and to_char(oi.business_date, 'YYYY-MM') = %s
          and bs.type = 'baito'
          and coalesce(c.is_drink_back, false) = false
          and bs.parent_id is not null
          and trim(bs.parent_id::text) <> ''
          and (bs.parent_id_2 is null or trim(bs.parent_id_2::text) = '')
          and oi.credit_staff_id::text <> bs.parent_id::text
    """
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, [year_month])
        affected = cur.rowcount
        conn.commit()
        return affected