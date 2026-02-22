from collections import defaultdict
from repositories.staff_repository import StaffRepository
from repositories.sales_repository import SalesRepository
from repositories.category_repository import CategoryRepository


class SalesDistributionService:

    @staticmethod
    def calculate():

        staff_list = StaffRepository.load_all()
        sales_list = SalesRepository.load_all()
        category_master = CategoryRepository.load()

        # --------------------------------------
        # ① 個人売上金額（カテゴリ別も保持）
        # --------------------------------------
        personal_sales_amount = defaultdict(float)
        personal_sales_detail = defaultdict(lambda: defaultdict(float))

        for sale in sales_list:
            personal_sales_amount[sale.staff_id] += sale.amount
            personal_sales_detail[sale.staff_id][sale.category] += sale.amount

        # --------------------------------------
        # ② 個人売上F計算
        # --------------------------------------
        personal_sales_f = {}

        for staff in staff_list:
            sid = staff.id
            total_f = 0

            for category, amount in personal_sales_detail[sid].items():
                f_rate = category_master.get(category, {}).get("rate", 0)
                total_f += amount * f_rate

            personal_sales_f[sid] = total_f

        # --------------------------------------
        # ③ 子のFを均等分配
        # --------------------------------------
        children_sales_f = defaultdict(float)

        for child in staff_list:

            if not child.parents:
                continue

            child_f = personal_sales_f.get(child.id, 0)
            parent_count = len(child.parents)

            share = child_f / parent_count if parent_count > 0 else 0

            for parent_id in child.parents:
                children_sales_f[parent_id] += share
        
        # --------------------------------------
        # ③-2 子の売上金額を均等分配
        # --------------------------------------
        children_sales_amount = defaultdict(float)

        for child in staff_list:

            if not child.parents:
                continue

            child_amount = personal_sales_amount.get(child.id, 0)
            parent_count = len(child.parents)

            share = child_amount / parent_count if parent_count > 0 else 0

            for parent_id in child.parents:
                children_sales_amount[parent_id] += share


        # --------------------------------------
        # ④ 組織売上F
        # --------------------------------------
        result = {}

        for staff in staff_list:
            sid = staff.id

            pf = personal_sales_f.get(sid, 0)
            cf = children_sales_f.get(sid, 0)

                    # --------------------------------------
        # ④ 組織売上F ＋ 組織売上金額
        # --------------------------------------
        result = {}

        for staff in staff_list:
            sid = staff.id

            pf = personal_sales_f.get(sid, 0)
            cf = children_sales_f.get(sid, 0)

            pa = personal_sales_amount.get(sid, 0)
            ca = children_sales_amount.get(sid, 0)

            result[sid] = {
                "personal_sales_amount": pa,
                "personal_sales_detail": personal_sales_detail.get(sid, {}),
                "children_sales_amount": ca,
                "personal_sales_f": pf,
                "children_sales_f": cf,
                "org_sales_f": pf + cf,
            }

        return result