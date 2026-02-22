import pandas as pd
from repositories.staff_repository import StaffRepository
from models.staff import Staff

class StaffSyncService:

    @staticmethod
    def sync_from_pos(uploaded_file):

        df = pd.read_csv(uploaded_file)

        # activeのみ対象
        df = df[df["status"] == "active"]

        existing = {s.id: s for s in StaffRepository.load_all()}

        for _, row in df.iterrows():

            staff_id = str(row["staffId"])
            name = row["name"]
            staff_type = row["type"]  # staff / baito

            if staff_id not in existing:
                existing[staff_id] = Staff(
                    id=staff_id,
                    name=name,
                    type=staff_type,
                    parents=[],
                    transportation_cost=0,
                    working_hours=0.0
                )
            else:
                # 名前やタイプ更新
                existing[staff_id].name = name
                existing[staff_id].type = staff_type

        StaffRepository.save_all(list(existing.values()))
