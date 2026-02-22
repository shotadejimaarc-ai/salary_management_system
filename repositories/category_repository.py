import json
import os

FILE_PATH = "category_master.json"

class CategoryRepository:

    @staticmethod
    def load():
        if not os.path.exists(FILE_PATH):
            return {}

        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save(data):
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)



    