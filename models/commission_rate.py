from dataclasses import dataclass

@dataclass
class CommissionRate:
    min_amount: int
    max_amount: int
    rate: float
