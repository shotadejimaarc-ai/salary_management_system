from database import get_connection
from datetime import datetime


class SalaryRepository:

    @staticmethod
    def save_confirmed_salary(staff_id, year, month, amount):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO salary_records (staff_id, year, month, amount, confirmed, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
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