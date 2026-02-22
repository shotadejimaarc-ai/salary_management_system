from services.sales_distribution_service import SalesDistributionService


class SalesService:

    @staticmethod
    def get_monthly_sales_summary_by_staff(staff_id, target_month):

        # 🔥 月を渡す
        distribution = SalesDistributionService.calculate(target_month)

        staff_data = distribution.get(staff_id, {})

        personal_amount = staff_data.get("personal_sales_amount", 0)
        children_amount = staff_data.get("children_sales_amount", 0)

        org_amount = personal_amount + children_amount

        return {
            "personal_sales_amount": personal_amount,
            "personal_sales_detail": staff_data.get("personal_sales_detail", {}),
            "personal_sales_f": staff_data.get("personal_sales_f", 0),
            "children_sales_amount": children_amount,
            "children_sales_f": staff_data.get("children_sales_f", 0),
            "org_sales_amount": org_amount,
            "org_sales_f": staff_data.get("org_sales_f", 0),
        }