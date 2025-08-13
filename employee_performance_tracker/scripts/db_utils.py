import os
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def get_engine(db_dialect: Optional[str] = None) -> Engine:
    db_dialect = (db_dialect or os.getenv("DB_DIALECT", "sqlite")).lower()
    if db_dialect in {"sqlite", "sqlite3"}:
        base_dir = Path(__file__).resolve().parents[1]
        data_dir = base_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        sqlite_path = data_dir / "employee_performance.sqlite"
        url = f"sqlite:///{sqlite_path}"
        return create_engine(url)
    if db_dialect in {"postgres", "postgresql", "pg"}:
        user = os.getenv("POSTGRES_USER", "ep_user")
        password = os.getenv("POSTGRES_PASSWORD", "ep_pass")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = int(os.getenv("POSTGRES_PORT", "5432"))
        db = os.getenv("POSTGRES_DB", "employee_performance")
        url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
        return create_engine(url, pool_pre_ping=True)
    raise ValueError("Unsupported DB_DIALECT. Use sqlite or postgresql.")


def load_dataframe(df: pd.DataFrame, engine: Engine, table_name: str) -> None:
    df.to_sql(table_name, engine, if_exists="replace", index=False, method="multi")


def run_top5_query(engine: Engine, table_name: str) -> pd.DataFrame:
    query = text(
        f"""
        SELECT
            "Employee ID" AS employee_id,
            "Name" AS name,
            "Department" AS department,
            "KPI score" AS kpi_score,
            "Attendance %" AS attendance_percent
        FROM {table_name}
        ORDER BY "KPI score" DESC, "Attendance %" DESC
        LIMIT 5
        """
    )
    with engine.connect() as conn:
        return pd.read_sql(query, conn)