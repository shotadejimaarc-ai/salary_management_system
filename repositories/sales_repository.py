from database import get_connection
from models.sale import Sale


class SalesRepository:

    # =============================
    # 保存
    # =============================
    @staticmethod
    def save(sale: Sale):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sales 
            (sales_date, staff_id, staff_name, category, product_name, amount)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            sale.sales_date,
            sale.staff_id,
            sale.staff_name,
            sale.category,
            sale.product_name,
            sale.amount
        ))

        conn.commit()
        conn.close()


    # =============================
    # 全件取得
    # =============================
    @staticmethod
    def load_all():
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM sales ORDER BY sales_date DESC")
        rows = cursor.fetchall()

        conn.close()

        return [
            Sale(
                sales_date=row["sales_date"],
                staff_id=row["staff_id"],
                staff_name=row["staff_name"],
                category=row["category"],
                product_name=row["product_name"],
                amount=row["amount"]
            )
            for row in rows
        ]


    # =============================
    # 利用可能な月一覧取得（DB直）
    # =============================
    @staticmethod
    def get_available_months():
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT substr(sales_date, 1, 7) as month
            FROM sales
            ORDER BY month DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [row["month"] for row in rows]


    # =============================
    # スタッフ別取得（全期間）
    # =============================
    @staticmethod
    def find_by_staff(staff_id):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM sales
            WHERE staff_id = ?
            ORDER BY sales_date DESC
        """, (str(staff_id),))

        rows = cursor.fetchall()
        conn.close()

        return [
            Sale(
                sales_date=row["sales_date"],
                staff_id=row["staff_id"],
                staff_name=row["staff_name"],
                category=row["category"],
                product_name=row["product_name"],
                amount=row["amount"]
            )
            for row in rows
        ]


    # =============================
    # スタッフ＋月指定取得（🔥重要）
    # =============================
    @staticmethod
    def find_by_staff_and_month(staff_id, target_month):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM sales
            WHERE staff_id = ?
            AND sales_date LIKE ?
            ORDER BY sales_date DESC
        """, (str(staff_id), f"{target_month}%"))

        rows = cursor.fetchall()
        conn.close()

        return [
            Sale(
                sales_date=row["sales_date"],
                staff_id=row["staff_id"],
                staff_name=row["staff_name"],
                category=row["category"],
                product_name=row["product_name"],
                amount=row["amount"]
            )
            for row in rows
        ]


    # =============================
    # 全削除
    # =============================
    @staticmethod
    def delete_all():
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM sales")

        conn.commit()
        conn.close()