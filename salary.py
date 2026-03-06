import pandas as pd

def build_salary_table(staff_df: pd.DataFrame, drink_df: pd.DataFrame, hours_df: pd.DataFrame) -> pd.DataFrame:
    df = staff_df.copy()

    # drinkback
    if drink_df is not None and len(drink_df) > 0:
        df = df.merge(drink_df, on="staff_id", how="left")
    else:
        df["drinkback_total"] = 0

    # hours
    if hours_df is not None and len(hours_df) > 0:
        df = df.merge(hours_df, on="staff_id", how="left")
    else:
        df["total_hours"] = 0

    # numeric
    df["drinkback_total"] = pd.to_numeric(df.get("drinkback_total", 0), errors="coerce").fillna(0)
    df["total_hours"] = pd.to_numeric(df.get("total_hours", 0), errors="coerce").fillna(0)
    df["hourly_wage"] = pd.to_numeric(df.get("hourly_wage", 0), errors="coerce").fillna(0)
    df["transportation_allowance"] = pd.to_numeric(df.get("transportation_allowance", 0), errors="coerce").fillna(0)

    # salary
    df["salary"] = (df["hourly_wage"] * df["total_hours"]) + df["transportation_allowance"] + df["drinkback_total"]
    df["salary"] = df["salary"].round(0).astype(int)

    cols = ["staff_id", "name", "hourly_wage", "total_hours", "transportation_allowance", "drinkback_total", "salary"]
    return df[cols].rename(columns={"drinkback_total": "drinkback"})
