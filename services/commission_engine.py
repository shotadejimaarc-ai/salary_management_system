from repositories.staff_repository import StaffRepository
from repositories.sales_repository import SalesRepository

class CommissionEngine:

    @staticmethod
    def calculate():

        staff_list = StaffRepository.load_all()
        staff_map = {s.id: s for s in staff_list}

        sales = SalesRepository.load_all()

        result = {}

        for sale in sales:

            staff_id = sale["staff_id"]
            amount = sale["amount"]

            CommissionEngine._distribute(
                staff_id,
                amount,
                staff_map,
                result
            )

        return result


    @staticmethod
    def _distribute(staff_id, amount, staff_map, result):

        if staff_id not in result:
            result[staff_id] = 0

        result[staff_id] += amount

        staff = staff_map.get(staff_id)

        if not staff:
            return

        for parent_id in staff.parents:
            CommissionEngine._distribute(
                parent_id,
                amount * 0.1,  # 仮10%
                staff_map,
                result
            )
