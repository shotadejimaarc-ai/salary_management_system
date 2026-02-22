class SalaryUseCase:

    def __init__(self, salary_service, commission_service, allowance_service):
        self.salary_service = salary_service
        self.commission_service = commission_service
        self.allowance_service = allowance_service

    def calculate_salary(self, sales_dict):

        results = []

        for name, sales in sales_dict.items():

            # --- 型安全対策（CSVは文字列で来る可能性あり） ---
            try:
                sales = float(sales)
            except (ValueError, TypeError):
                sales = 0.0

            base_salary = 200000.0   # 仮の基本給
            rate = 0.1               # 仮の歩合率
            allowance = 10000.0      # 仮の固定手当

            commission = self.commission_service.calculate(sales, rate)

            total_salary = self.salary_service.calculate(
                base_salary,
                commission,
                allowance
            )

            results.append({
                "name": name,
                "sales": sales,
                "salary": total_salary
            })

        return results
