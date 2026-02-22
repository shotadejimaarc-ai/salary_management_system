import json
from database import get_connection
from models.sale import Sale

class SalesRepository:
    

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


    @staticmethod
    def load_all():
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM sales")
        rows = cursor.fetchall()

        sales_list = []

        for row in rows:
            sales_list.append(
                Sale(
                    sales_date=row["sales_date"],
                    staff_id=row["staff_id"],
                    staff_name=row["staff_name"],
                    category=row["category"],
                    product_name=row["product_name"],
                    amount=row["amount"]
                )
            )

        conn.close()
        return sales_list



    @staticmethod
    def find_by_staff(staff_id):
        staff_id = str(staff_id)
        sales = SalesRepository.load_all()

        return [
            s for s in sales
            if str(s.staff_id) == staff_id
        ]
    

    @staticmethod
    def delete_all():
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM sales")

        conn.commit()
        conn.close()

    @staticmethod
    def find_by_staff_and_month(staff_id, target_month):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM sales
            WHERE staff_id = ?
            AND sales_date LIKE ?
        """, (str(staff_id), f"{target_month}%"))

        rows = cursor.fetchall()

        sales_list = []

        for row in rows:
            sales_list.append(
                Sale(
                    sales_date=row["sales_date"],
                    staff_id=row["staff_id"],
                    staff_name=row["staff_name"],
                    category=row["category"],
                    product_name=row["product_name"],
                    amount=row["amount"]
                )
            )

        conn.close()
        return sales_list

