from pathlib import Path

import pandas as pd

from data_generation import generate_mock_employee_data, save_to_excel
from db_utils import get_engine, load_dataframe, run_top5_query
from analysis import clean_data, avg_kpi_by_dept, attendance_distribution
from viz import plot_avg_kpi_by_dept, plot_attendance_pie


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"
TABLE_NAME = "employee_performance"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    # Phase 1
    df = generate_mock_employee_data()
    excel_path = DATA_DIR / "employee_performance.xlsx"
    save_to_excel(df, excel_path)

    engine = get_engine()  # defaults to SQLite
    load_dataframe(df, engine, TABLE_NAME)

    top5 = run_top5_query(engine, TABLE_NAME)
    (OUTPUTS_DIR / "top5_by_kpi.csv").write_text(top5.to_csv(index=False))

    # Phase 2
    df_sql = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", engine)
    df_clean = clean_data(df_sql)

    avg_df = avg_kpi_by_dept(df_clean)
    dist_df = attendance_distribution(df_clean)

    plot_avg_kpi_by_dept(avg_df, OUTPUTS_DIR / "avg_kpi_by_department.png")
    plot_attendance_pie(dist_df, OUTPUTS_DIR / "attendance_category_distribution.png")

    df_clean.to_csv(OUTPUTS_DIR / "employee_performance_cleaned.csv", index=False)


if __name__ == "__main__":
    main()