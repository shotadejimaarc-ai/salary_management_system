import csv
import io
from datetime import datetime


class BankTransferService:

    @staticmethod
    def generate_transfer_data(staff_list):

        transfer_rows = []

        for staff in staff_list:

            # 金額計算（バイト想定）
            if staff.type == "baito":
                base_salary = staff.hourly_wage * staff.working_hours
                transport_total = staff.transportation_cost * staff.work_days * 2
                amount = int(base_salary + transport_total)
            else:
                continue

            # 必須チェック
            if not (
                staff.bank_code and
                staff.branch_code and
                staff.account_number and
                staff.account_holder_kana
            ):
                continue

            account_type_code = "1" if staff.account_type == "普通" else "2"

            transfer_rows.append([
                staff.bank_code.zfill(4),
                staff.branch_code.zfill(3),
                account_type_code,
                staff.account_number.zfill(7),
                staff.account_holder_kana,
                amount
            ])

        return transfer_rows


    @staticmethod
    def generate_csv(transfer_rows):

        output = io.StringIO()
        writer = csv.writer(output)

        # ヘッダー（銀行仕様に合わせて変更可）
        writer.writerow([
            "銀行コード",
            "支店コード",
            "口座種別",
            "口座番号",
            "受取人名",
            "振込金額"
        ])

        for row in transfer_rows:
            writer.writerow(row)

        return output.getvalue()