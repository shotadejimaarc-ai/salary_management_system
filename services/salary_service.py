class SalaryService:

    # ==========================================
    # 正社員給与計算（F制度）
    # ==========================================
    @staticmethod
    def calculate_staff_salary(staff, summary, commission_rules, category_master):

        # ==============================
        # ① 個人売上金額
        # ==============================
        personal_sales_amount = summary.get("personal_sales_amount", 0)

        # ==============================
        # ② 個人売上F
        # ==============================
        personal_sales_f = 0

        personal_sales_detail = summary.get("personal_sales_detail", {})

        for category, amount in personal_sales_detail.items():
            f_rate = category_master.get(category, {}).get("f_rate", 0)
            personal_sales_f += amount * f_rate
        
        # ==============================
        # ③ 組織売上金額
        # ==============================
        children_sales_amount = summary.get("children_sales_amount", 0)

        org_sales_amount = personal_sales_amount + children_sales_amount

        # ==============================
        # ② 組織売上F（summaryから直接取得）
        # ==============================
        org_sales_f = summary.get("org_sales_f", 0)
        personal_sales_amount = summary.get("personal_sales_amount", 0)

        # ==============================
        # ④ Fテーブルからレート取得
        # ==============================
        commission_rate = 0

        for rule in commission_rules:
            max_val = rule["max"] if rule["max"] is not None else float("inf")
            if org_sales_f >= rule["min"] and org_sales_f < max_val:
                commission_rate = rule["rate"]
                break

        # ==============================
        # ⑤ 総支給額
        # ==============================
        total = org_sales_f * commission_rate

        # 家賃（社員のみ）
        total -= 2000

        return {
            "type": "staff",
            "personal_sales_amount": personal_sales_amount,
            "org_sales_f": org_sales_f,
            "commission_rate": commission_rate,
            "total": total
        }

    # ==========================================
    # バイト給与
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
