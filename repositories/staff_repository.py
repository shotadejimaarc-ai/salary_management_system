from database import get_connection
from models.staff import Staff
import sqlite3


class StaffRepository:

    # ==========================
    # 全件取得
    # ==========================
    @staticmethod
    def load_all():
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM staff")
        rows = cursor.fetchall()

        staff_list = []

        for row in rows:
            staff_list.append(
                Staff(
                    id=row["id"],
                    name=row["name"],
                    type=row["type"],
                    parents=row["parents"].split(",") if row["parents"] else [],
                    payment_method=row["payment_method"] if "payment_method" in row.keys() else "bank",
                    transportation_cost=row["transportation_cost"],
                    working_hours=row["working_hours"],
                    bank_name=row["bank_name"] if "bank_name" in row.keys() else "",
                    bank_code=str(row["bank_code"]).zfill(4) if row["bank_code"] else "",
                    branch_name=row["branch_name"] if "branch_name" in row.keys() else "",
                    branch_code=str(row["branch_code"]).zfill(3) if row["branch_code"] else "",
                    account_type=row["account_type"] if "account_type" in row.keys() else "普通",
                    account_number=str(row["account_number"]).zfill(7) if row["account_number"] else "",
                    account_holder=row["account_holder"] if "account_holder" in row.keys() else "",
                    stock_balance=row["stock_balance"] if "stock_balance" in row.keys() else 0,
                )
            )

        conn.close()
        return staff_list


    # ==========================
    # 単体保存（新規 or 更新）
    # ==========================
    @staticmethod
    def save(staff: Staff):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            # 既存チェック
            cursor.execute("SELECT COUNT(*) FROM staff WHERE id = ?", (staff.id,))
            exists = cursor.fetchone()[0]

            if exists:
                # 更新
                cursor.execute("""
                    UPDATE staff SET
                        name=?,
                        type=?,
                        parents=?,
                        payment_method=?,
                        transportation_cost=?,
                        working_hours=?,
                        bank_name=?,
                        bank_code=?,
                        branch_name=?,
                        branch_code=?,
                        account_type=?,
                        account_number=?,
                        account_holder=?,
                        stock_balance=?
                    WHERE id=?
                """, (
                    staff.name,
                    staff.type,
                    ",".join(staff.parents),
                    staff.payment_method,
                    staff.transportation_cost,
                    staff.working_hours,
                    staff.bank_name,
                    staff.bank_code,
                    staff.branch_name,
                    staff.branch_code,
                    staff.account_type,
                    staff.account_number,
                    staff.account_holder,
                    staff.stock_balance,
                    staff.id
                ))
            else:
                # 新規
                cursor.execute("""
                    INSERT INTO staff (
                        id,
                        name,
                        type,
                        parents,
                        payment_method,
                        transportation_cost,
                        working_hours,
                        bank_name,
                        bank_code,
                        branch_name,
                        branch_code,
                        account_type,
                        account_number,
                        account_holder,
                        stock_balance
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    staff.id,
                    staff.name,
                    staff.type,
                    ",".join(staff.parents),
                    staff.payment_method,
                    staff.transportation_cost,
                    staff.working_hours,
                    staff.bank_name,
                    staff.bank_code,
                    staff.branch_name,
                    staff.branch_code,
                    staff.account_type,
                    staff.account_number,
                    staff.account_holder,
                    staff.stock_balance,
                ))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            conn.close()


    # ==========================
    # 全削除→再保存（既存互換）
    # ==========================
    @staticmethod
    def save_all(staff_list):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM staff")

            for staff in staff_list:
                cursor.execute("""
                    INSERT INTO staff (
                        id,
                        name,
                        type,
                        parents,
                        payment_method,
                        transportation_cost,
                        working_hours,
                        bank_name,
                        bank_code,
                        branch_name,
                        branch_code,
                        account_type,
                        account_number,
                        account_holder,
                        stock_balance
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    staff.id,
                    staff.name,
                    staff.type,
                    ",".join(staff.parents),
                    staff.payment_method,
                    staff.transportation_cost,
                    staff.working_hours,
                    staff.bank_name,
                    staff.bank_code,
                    staff.branch_name,
                    staff.branch_code,
                    staff.account_type,
                    staff.account_number,
                    staff.account_holder,
                    staff.stock_balance,
                ))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            conn.close()


    # ==========================
    # ID取得
    # ==========================
    @staticmethod
    def get_by_id(staff_id):
        staff_list = StaffRepository.load_all()

        for staff in staff_list:
            if staff.id == staff_id:
                return staff

        return None