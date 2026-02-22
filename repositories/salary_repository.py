from database import get_connection
from datetime import datetime


class SalaryRepository:

    # ===============================
    # 新設計（推奨）
    # ===============================

    @staticmethod
    def save_confirmed_salary(staff_id, year, month, amount):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO salary_records
            (staff_id, year, month, amount, confirmed, locked, created_at)
            VALUES (?, ?, ?, ?, 1, 0, ?)
            ON CONFLICT(staff_id, year, month)
            DO UPDATE SET
                amount=excluded.amount,
                confirmed=1
        """, (
            staff_id,
            year,
            month,
            amount,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()


    @staticmethod
    def get_confirmed_salaries(year, month):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM salary_records
            WHERE year=? AND month=? AND confirmed=1 AND locked=0
        """, (year, month))

        rows = cursor.fetchall()
        conn.close()
        return rows


    @staticmethod
    def lock_salary(year, month):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE salary_records
            SET locked=1
            WHERE year=? AND month=?
        """, (year, month))

        conn.commit()
        conn.close()


    # ===============================
    # 旧互換（安全用）
    # ===============================

    @staticmethod
    def confirm_salary(staff_id, period, total_amount):
        year, month = map(int, period.split("-"))
        SalaryRepository.save_confirmed_salary(
            staff_id,
            year,
            month,
            total_amount
        )


    @staticmethod
    def get_confirmed(period):
        year, month = map(int, period.split("-"))
        return SalaryRepository.get_confirmed_salaries(year, month)


    @staticmethod
    def is_confirmed(staff_id, period):
        year, month = map(int, period.split("-"))

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 1 FROM salary_records
            WHERE staff_id=? AND year=? AND month=? AND confirmed=1
        """, (staff_id, year, month))

        result = cursor.fetchone()
        conn.close()

        return result is not None