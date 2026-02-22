from services.commission_interface import CommissionCalculator

class CommissionService(CommissionCalculator):

    def calculate(self, sales: float, rate: float) -> float:
        return sales * rate
