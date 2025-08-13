import os
import time
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import matplotlib.pyplot as plt

# -----------------------------
# Configuration
# -----------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

DB_DIALECT = os.getenv("DB_DIALECT", "postgresql").lower()
DB_USER = os.getenv("POSTGRES_USER", "ep_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "ep_pass")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB", "employee_performance")
TABLE_NAME = "employee_performance"

if DB_DIALECT in {"postgres", "postgresql", "pg"}:
    CONNECTION_URL = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    DB_FLAVOR = "postgresql"
elif DB_DIALECT in {"sqlite", "sqlite3"}:
    sqlite_path = DATA_DIR / "employee_performance.sqlite"
    CONNECTION_URL = f"sqlite:///{sqlite_path}"
    DB_FLAVOR = "sqlite"
else:
    raise ValueError(
        "Unsupported DB_DIALECT. Use one of: postgresql, postgres, pg, sqlite, sqlite3"
    )

# -----------------------------
# Data generation
# -----------------------------

def generate_mock_employee_data(num_employees: int = 200, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    departments = [
        "Sales",
        "Engineering",
        "HR",
        "Marketing",
        "Finance",
        "Operations",
        "Support",
    ]
    department_probs = np.array([0.18, 0.32, 0.06, 0.12, 0.1, 0.14, 0.08])

    first_names = [
        "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Cameron", "Avery",
        "Jamie", "Drew", "Quinn", "Rowan", "Hayden", "Reese", "Blake", "Parker",
        "Logan", "Skyler", "Elliot", "Sawyer",
    ]
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    ]

    # Create IDs
    employee_ids = [f"E{idx:04d}" for idx in range(1, num_employees + 1)]

    # Create names
    names = [
        f"{rng.choice(first_names)} {rng.choice(last_names)}" for _ in range(num_employees)
    ]

    # Departments
    assigned_departments = rng.choice(departments, size=num_employees, p=department_probs)

    # KPI score: normal distribution centered around 75 with sd 10; clipped to [40, 100]
    kpi_scores = np.clip(rng.normal(loc=75, scale=10, size=num_employees), 40, 100)

    # Attendance %: skewed higher; beta distribution scaled to [60, 100]
    attendance = 60 + 40 * rng.beta(a=5, b=2, size=num_employees)

    # Last Training Date: within last 365 days
    days_back = rng.integers(low=0, high=365, size=num_employees)
    last_training = pd.Timestamp.today().normalize() - pd.to_timedelta(days_back, unit="D")

    df = pd.DataFrame(
        {
            "Employee ID": employee_ids,
            "Name": names,
            "Department": assigned_departments,
            "KPI score": np.round(kpi_scores, 2),
            "Attendance %": np.round(attendance, 1),
            "Last Training Date": last_training,
        }
    )

    return df


def save_to_excel(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Employees", index=False)


# -----------------------------
# Database helpers
# -----------------------------

def get_engine() -> Engine:
    return create_engine(CONNECTION_URL, pool_pre_ping=True)


def wait_for_db(engine: Engine, timeout_seconds: int = 60) -> None:
    if DB_FLAVOR == "sqlite":
        return  # no wait needed for SQLite
    start = time.time()
    last_err = None
    while time.time() - start < timeout_seconds:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(1.5)
    raise TimeoutError(f"Database not reachable within {timeout_seconds}s: {last_err}")


def load_dataframe_to_postgres(df: pd.DataFrame, engine: Engine, table_name: str) -> None:
    # Use consistent dtypes
    dtype_map = {
        "Employee ID": pd.StringDtype(),
        "Name": pd.StringDtype(),
        "Department": pd.StringDtype(),
        "KPI score": "float",
        "Attendance %": "float",
        "Last Training Date": "datetime64[ns]",
    }

    df_for_sql = df.astype(dtype_map)

    # Load via to_sql
    df_for_sql.to_sql(
        table_name,
        engine,
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=5_000,
    )


# -----------------------------
# Analytics & visualization
# -----------------------------

def load_from_sql(engine: Engine, table_name: str) -> pd.DataFrame:
    query = text(f"SELECT * FROM {table_name}")
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df


def clean_and_derive(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()

    # Standardize column names to snake_case
    rename_map = {
        "Employee ID": "employee_id",
        "Name": "name",
        "Department": "department",
        "KPI score": "kpi_score",
        "Attendance %": "attendance_percent",
        "Last Training Date": "last_training_date",
    }
    df.rename(columns=rename_map, inplace=True)

    # Types
    df["last_training_date"] = pd.to_datetime(df["last_training_date"], errors="coerce")
    df["kpi_score"] = pd.to_numeric(df["kpi_score"], errors="coerce")
    df["attendance_percent"] = pd.to_numeric(df["attendance_percent"], errors="coerce")

    # Drop duplicates by employee_id keeping the latest training date
    df.sort_values(["employee_id", "last_training_date"], ascending=[True, False], inplace=True)
    df = df.drop_duplicates(subset=["employee_id"], keep="first").reset_index(drop=True)

    # Attendance categories
    def categorize_attendance(value: float) -> str:
        if pd.isna(value):
            return "Unknown"
        if value >= 90:
            return "High"
        if value >= 75:
            return "Medium"
        return "Low"

    df["attendance_category"] = df["attendance_percent"].apply(categorize_attendance)

    return df


def compute_avg_kpi_by_department(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby("department", dropna=False)["kpi_score"].mean().round(2).reset_index()
    )
    grouped.sort_values("kpi_score", ascending=False, inplace=True)
    return grouped


def compute_attendance_category_distribution(df: pd.DataFrame) -> pd.DataFrame:
    counts = df["attendance_category"].value_counts(dropna=False).rename_axis("category").reset_index(name="count")
    counts.sort_values("category", inplace=True)
    return counts


def plot_avg_kpi_bar(avg_kpi_df: pd.DataFrame, out_path: Path) -> None:
    plt.figure(figsize=(10, 6))
    bars = plt.bar(avg_kpi_df["department"], avg_kpi_df["kpi_score"], color="#4C78A8")
    plt.title("Average KPI by Department")
    plt.xlabel("Department")
    plt.ylabel("Average KPI Score")
    plt.xticks(rotation=30, ha="right")

    # Add labels on bars
    for bar in bars:
        height = bar.get_height()
        plt.annotate(f"{height:.1f}", xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_attendance_category_pie(dist_df: pd.DataFrame, out_path: Path) -> None:
    plt.figure(figsize=(7, 7))
    labels = dist_df["category"].tolist()
    sizes = dist_df["count"].tolist()
    colors = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2"]
    plt.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140, colors=colors[: len(sizes)])
    plt.title("Attendance Category Distribution")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


# -----------------------------
# Orchestration
# -----------------------------

def run_top5_query(engine: Engine, out_csv: Path) -> pd.DataFrame:
    query = text(
        f"""
        SELECT
            "Employee ID" AS employee_id,
            "Name" AS name,
            "Department" AS department,
            "KPI score" AS kpi_score,
            "Attendance %" AS attendance_percent
        FROM {TABLE_NAME}
        ORDER BY "KPI score" DESC, "Attendance %" DESC
        LIMIT 5
        """
    )
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    df.to_csv(out_csv, index=False)
    return df


def main() -> Tuple[Path, Path, Path]:
    # Phase 1: Generate and load
    print("Generating mock employee data...")
    df_mock = generate_mock_employee_data(num_employees=200, seed=42)

    excel_path = DATA_DIR / "employee_performance.xlsx"
    save_to_excel(df_mock, excel_path)
    print(f"Saved mock data to: {excel_path}")

    print(f"Connecting to database via {DB_FLAVOR}...")
    engine = get_engine()
    wait_for_db(engine, timeout_seconds=90)

    print("Loading dataframe to SQL table...")
    load_dataframe_to_postgres(df_mock, engine, TABLE_NAME)
    print(f"Loaded {len(df_mock)} rows into table '{TABLE_NAME}'.")

    print("Running sample SQL query: Top 5 employees by KPI...")
    top5_csv = OUTPUTS_DIR / "top5_by_kpi.csv"
    top5_df = run_top5_query(engine, top5_csv)
    print(top5_df)
    print(f"Saved top 5 results to: {top5_csv}")

    # Phase 2: Processing & Viz
    print("Loading data back from SQL for analysis...")
    df_sql = load_from_sql(engine, TABLE_NAME)
    df_clean = clean_and_derive(df_sql)

    avg_kpi_df = compute_avg_kpi_by_department(df_clean)
    attendance_dist_df = compute_attendance_category_distribution(df_clean)

    bar_out = OUTPUTS_DIR / "avg_kpi_by_department.png"
    pie_out = OUTPUTS_DIR / "attendance_category_distribution.png"

    print("Creating visualizations...")
    plot_avg_kpi_bar(avg_kpi_df, bar_out)
    plot_attendance_category_pie(attendance_dist_df, pie_out)

    cleaned_csv = OUTPUTS_DIR / "employee_performance_cleaned.csv"
    df_clean.to_csv(cleaned_csv, index=False)

    print(f"Saved cleaned dataset to: {cleaned_csv}")
    print(f"Saved charts to: {bar_out} and {pie_out}")

    return cleaned_csv, bar_out, pie_out


if __name__ == "__main__":
    main()