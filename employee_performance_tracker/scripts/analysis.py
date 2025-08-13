import pandas as pd


def clean_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    df = df.rename(
        columns={
            "Employee ID": "employee_id",
            "Name": "name",
            "Department": "department",
            "KPI score": "kpi_score",
            "Attendance %": "attendance_percent",
            "Last Training Date": "last_training_date",
        }
    )
    df["last_training_date"] = pd.to_datetime(df["last_training_date"], errors="coerce")
    df["kpi_score"] = pd.to_numeric(df["kpi_score"], errors="coerce")
    df["attendance_percent"] = pd.to_numeric(df["attendance_percent"], errors="coerce")

    def cat(a: float) -> str:
        if pd.isna(a):
            return "Unknown"
        if a >= 90:
            return "High"
        if a >= 75:
            return "Medium"
        return "Low"

    df["attendance_category"] = df["attendance_percent"].apply(cat)
    return df


def avg_kpi_by_dept(df: pd.DataFrame) -> pd.DataFrame:
    out = df.groupby("department")["kpi_score"].mean().round(2).reset_index()
    return out.sort_values("kpi_score", ascending=False)


def attendance_distribution(df: pd.DataFrame) -> pd.DataFrame:
    return df["attendance_category"].value_counts().rename_axis("category").reset_index(name="count")