# services/org_sales_detail_service.py

class OrgSalesDetailService:

    @staticmethod
    def build_detail(selected_staff, staff_list, sales_summary):
        """
        下部表示専用
        ・選択担当者の売上
        ・子担当者の売上
        ・親分配率表示（50% or 100%）
        """

        detail_list = []

        # ==============================
        # ① 選択担当者本人の売上
        # ==============================
        for sale in sales_summary.get("sales_list", []):
            detail_list.append({
                "staff_name": selected_staff.name,
                "amount": sale["amount"],
                "allocation_rate": 1.0  # 本人は100%
            })

        # ==============================
        # ② 子担当者抽出
        # ==============================
        children = [
            s for s in staff_list
            if getattr(s, "parent_ids", []) and selected_staff.id in s.parent_ids
        ]

        for child in children:

            child_summary = sales_summary.get("children_sales", {}).get(child.id, [])

            # 親人数チェック
            parent_count = len(getattr(child, "parent_ids", []))

            allocation_rate = 1.0
            if parent_count >= 2:
                allocation_rate = 0.5

            for sale in child_summary:
                detail_list.append({
                    "staff_name": child.name,
                    "amount": sale["amount"],
                    "allocation_rate": allocation_rate
                })

        return detail_list
