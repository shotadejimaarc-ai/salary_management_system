from database import get_connection
from models.commission_rate import CommissionRate

class CommissionRateRepository:

    @staticmethod
    def load_all():
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM commission_rates")
        rows = cursor.fetchall()

        conn.close()

        return rows
