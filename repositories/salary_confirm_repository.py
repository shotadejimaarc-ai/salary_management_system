# repositories/salary_confirm_repository.py

import json
import os
from database import get_connection
import sqlite3

FILE_PATH = "data/salary_confirms.json"


class SalaryConfirmRepository:

    @staticmethod
    def load():
        if not os.path.exists(FILE_PATH):
            return []
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save(data):
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ------------------------------
    # 確定（上書き保存）
    # ------------------------------
    @staticmethod
    def confirm(staff_id, year, month, total):
        data = SalaryConfirmRepository.load()

        month_str = f"{year}-{str(month).zfill(2)}"

        # 既存削除（重複防止）
        data = [
            d for d in data
            if not (d["staff_id"] == staff_id and d["month"] == month_str)
        ]

        data.append({
            "staff_id": staff_id,
            "year": year,
            "month": month_str,
            "total": total,
            "status": "confirmed"
        })

        SalaryConfirmRepository.save(data)

    # ------------------------------
    # 1件取得
    # ------------------------------
    @staticmethod
    def find(staff_id, year, month):
        data = SalaryConfirmRepository.load()
        month_str = f"{year}-{str(month).zfill(2)}"

        for d in data:
            if d["staff_id"] == staff_id and d["month"] == month_str:
                return d
        return None

    # ------------------------------
    # 月単位取得
    # ------------------------------
    @staticmethod
    def get_confirmed_by_month(year, month):
        data = SalaryConfirmRepository.load()
        month_str = f"{year}-{str(month).zfill(2)}"
        return [d for d in data if d["month"] == month_str]
    

    # ==========================
    # 確定解除（JSON版）
    # ==========================
    @staticmethod
    def cancel(staff_id, year, month):
        data = SalaryConfirmRepository.load()
        month_str = f"{year}-{str(month).zfill(2)}"

        # 該当データ削除
        new_data = [
            d for d in data
            if not (d["staff_id"] == staff_id and d["month"] == month_str)
        ]

        SalaryConfirmRepository.save(new_data)