import sqlite3

DB_PATH = "salary.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # ===== staff =====
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staff (
        id TEXT PRIMARY KEY,
        name TEXT,
        type TEXT,
        parents TEXT,
        transportation_cost INTEGER DEFAULT 0,
        working_hours REAL DEFAULT 0,

        bank_name TEXT,
        bank_code TEXT,
        branch_name TEXT,
        branch_code TEXT,
        account_type TEXT,
        account_number TEXT,
        account_holder TEXT
    )
    """)


    # ===== sales =====
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sales_date TEXT NOT NULL,
        staff_id TEXT NOT NULL,
        staff_name TEXT NOT NULL,
        category TEXT NOT NULL,
        product_name TEXT NOT NULL,
        amount INTEGER NOT NULL
    )
    """)

    # ===== commission_rates =====
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS commission_rates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        min_amount INTEGER,
        max_amount INTEGER,
        rate REAL
    )
    """)

    # ===== salary_confirmations =====
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS salary_confirmations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        staff_id TEXT NOT NULL,
        period TEXT NOT NULL,
        total_amount INTEGER NOT NULL,
        confirmed_at TEXT NOT NULL,
        UNIQUE(staff_id, period)  
    )
    """)

    # ===== salary_records =====
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS salary_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        staff_id TEXT NOT NULL,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        amount INTEGER NOT NULL,
        confirmed INTEGER DEFAULT 0,
        locked INTEGER DEFAULT 0,
        created_at TEXT,
        UNIQUE(staff_id, year, month)
    )
    """)

    # ===== bank transfer logs =====
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bank_transfer_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year INTEGER,
        month INTEGER,
        total_amount INTEGER,
        transfer_date TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

    # 🔥 ここで migration 実行
    migrate_staff_table()


# ==========================
# migration（外に出す）
# ==========================
def migrate_staff_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(staff)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    new_columns = [
        ("bank_name", "TEXT"),
        ("bank_code", "TEXT"),
        ("branch_name", "TEXT"),
        ("branch_code", "TEXT"),
        ("account_type", "TEXT"),
        ("account_number", "TEXT"),
        ("account_holder", "TEXT"),
        ("payment_method", "TEXT DEFAULT 'bank'"),
        ("stock_balance", "INTEGER DEFAULT 0"),
    ]

    for col_name, col_def in new_columns:
        if col_name not in existing_columns:
            print(f"Adding column: {col_name}")
            cursor.execute(
                f"ALTER TABLE staff ADD COLUMN {col_name} {col_def}"
            )

    conn.commit()
    conn.close()