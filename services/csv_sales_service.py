import pandas as pd
from models.sale import Sale
from repositories.sales_repository import SalesRepository

class CsvSalesService:

    def import_csv(self, file):
        df = pd.read_csv(file)

        exclude_columns = ["席", "数量", "単価"]

        for _, row in df.iterrows():

            data = {
                col: row[col]
                for col in df.columns
                if col not in exclude_columns
            }

            sale = Sale(
                staff_id=str(row["担当ID"]),
                amount=int(row["金額"]),
                data=data
            )

            SalesRepository.save(sale)
