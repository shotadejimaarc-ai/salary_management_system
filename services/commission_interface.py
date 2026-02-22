from abc import ABC, abstractmethod

class CommissionCalculator(ABC):

    @abstractmethod
    def calculate(self, sales: float, rate: float) -> float:
        pass
