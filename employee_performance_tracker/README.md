# Employee Performance Tracker

Phases covered:
- Phase 1 (SQL): Generate mock data (Excel), load into PostgreSQL (or SQLite fallback), run a sample query (Top 5 by KPI)
- Phase 2 (Python): Load from SQL with Pandas, clean/compute, create 2 charts, save PNGs and cleaned CSV
- Phase 3 (Power BI): Load cleaned CSV and recreate charts with a Department slicer

## Prerequisites
- Python 3.10+
- Optional: Docker (to run PostgreSQL). If unavailable, the pipeline will use SQLite automatically.

## Quickstart

### Option A: PostgreSQL via Docker (recommended)

```bash
docker run -d --name employee_postgres \
  -e POSTGRES_USER=ep_user \
  -e POSTGRES_PASSWORD=ep_pass \
  -e POSTGRES_DB=employee_performance \
  -p 5432:5432 \
  -v /workspace/employee_performance_tracker/pgdata:/var/lib/postgresql/data \
  postgres:16
# Run with Postgres (default)
DB_DIALECT=postgresql python /workspace/employee_performance_tracker/scripts/employee_pipeline.py
```

### Option B: SQLite fallback (no Docker/root required)

```bash
DB_DIALECT=sqlite python /workspace/employee_performance_tracker/scripts/employee_pipeline.py
```

Outputs:
- Excel data: `data/employee_performance.xlsx`
- Top 5 by KPI (CSV): `outputs/top5_by_kpi.csv`
- Visualizations: `outputs/avg_kpi_by_department.png`, `outputs/attendance_category_distribution.png`
- Cleaned dataset for Power BI: `outputs/employee_performance_cleaned.csv`

## Dependencies
If virtualenv cannot be created due to missing system packages, install user-local packages:

```bash
pip3 install --user --upgrade pip setuptools wheel
pip3 install --user -r /workspace/employee_performance_tracker/requirements.txt
```

Then run the pipeline using the same Python:

```bash
DB_DIALECT=sqlite python3 /workspace/employee_performance_tracker/scripts/employee_pipeline.py
```

## Power BI (Phase 3)
- Load `outputs/employee_performance_cleaned.csv` into Power BI
- Create:
  - Bar chart: Axis = `department`, Values = average of `kpi_score`
  - Pie chart: Legend = `attendance_category`, Values = `count of employee_id` (or `count of name`)
- Add a slicer: Field = `department`