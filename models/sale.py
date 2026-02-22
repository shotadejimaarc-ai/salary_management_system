from dataclasses import dataclass

@dataclass
class Sale:
    sales_date: str
    staff_id: str
    staff_name: str
    category: str
    product_name: str
    amount: int


