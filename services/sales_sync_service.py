from models.sale import Sale
from repositories.sales_repository import SalesRepository

class SalesSyncService:

    @staticmethod
    def sync_from_df(df):

        df = df.rename(columns={
            "営業日": "sales_date",
            "担当ID": "staff_id",
            "担当名": "staff_name",
            "カテゴリ": "category",
            "商品名": "product_name",
            "金額": "amount"
        })

        required_columns = [
            "sales_date",
            "staff_id",
            "staff_name",
            "category",
            "product_name",
            "amount"
        ]

        for col in required_columns:
            if col not in df.columns:
                raise Exception(f"{col} 列がCSVに存在しません")

        for _, row in df.iterrows():

            sale = Sale(
                sales_date=row["sales_date"],
                staff_id=row["staff_id"],
                staff_name=row["staff_name"],
                category=row["category"],
                product_name=row["product_name"],
                amount=int(row["amount"])
            )

            SalesRepository.save(sale)
