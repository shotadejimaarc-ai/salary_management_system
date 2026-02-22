from dataclasses import dataclass
from typing import List

@dataclass
class Staff:
    id: str
    name: str
    type: str  # "staff" or "baito"
    parents: List[str]

    payment_method: str = "bank"

    transportation_cost: int = 0
    working_hours: float = 0.0

    # ===== 銀行振込情報 =====
    bank_name: str = ""
    bank_code: str = ""
    branch_name: str = ""
    branch_code: str = ""
    account_type: str = "普通"  # 普通 / 当座
    account_number: str = ""
    account_holder: str = ""  # カナ

    stock_balance: int = 0

    


    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "parents": ",".join(self.parents) if self.parents else "",
            "payment_method": self.payment_method,
            "transportation_cost": self.transportation_cost,
            "working_hours": self.working_hours,
            

            # 追加
            "bank_name": self.bank_name,
            "bank_code": self.bank_code,
            "branch_name": self.branch_name,
            "branch_code": self.branch_code,
            "account_type": self.account_type,
            "account_number": self.account_number,
            "account_holder": self.account_holder,

            "stock_balance": self.stock_balance,
        }
