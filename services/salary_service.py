class SalaryService:

    # ==========================================
    # 正社員給与計算（F制度）
    # ==========================================
    @staticmethod
    def calculate_staff_salary(staff, summary, commission_rules, category_master):

        personal_sales_amount = summary.get("personal_sales_amount", 0)

        personal_sales_f = summary.get("personal_sales_f", 0)
        children_sales_amount = summary.get("children_sales_amount", 0)
        children_sales_f = summary.get("children_sales_f", 0)

        org_sales_amount = personal_sales_amount + children_sales_amount
        org_sales_f = personal_sales_f + children_sales_f

        # ===== レート判定（最重要修正版） =====
        commission_rate = 0

        commission_rules = sorted(commission_rules, key=lambda x: x["min"])

        for rule in commission_rules:
            min_val = rule.get("min", 0)
            max_val = rule.get("max")
            rate = rule.get("rate", 0)

            # ％登録対策（70 → 0.7）
            if rate > 1:
                rate = rate / 100

            if max_val is None:
                if org_sales_f >= min_val:
                    commission_rate = rate
                    break
            else:
                if min_val <= org_sales_f <= max_val:
                    commission_rate = rate
                    break

        total = org_sales_f * commission_rate
        total -= 2000

        return {
            "type": "staff",
            "personal_sales_amount": int(personal_sales_amount),
            "personal_sales_f": int(personal_sales_f),
            "org_sales_amount": int(org_sales_amount),
            "org_sales_f": int(org_sales_f),
            "commission_rate": commission_rate,
            "total": int(total)
        }

    # ==========================================
    # バイト給与計算
    # ==========================================
    @staticmethod
    def calculate_part_time_salary(staff, summary, category_master):

        hourly = getattr(staff, "hourly_wage", 0)
        hours = getattr(staff, "working_hours", 0)
        transportation = getattr(staff, "transportation_cost", 0)

        base_salary = hourly * hours

        # ドリンクバックのみ加算
        drink_back_total = summary.get("drink_back_total", 0)

        total = base_salary + transportation + drink_back_total

        return {
            "type": "part_time",
            "total": total,
            "base_salary": base_salary,
            "transportation": transportation,
            "drink_back_total": drink_back_total
        }