# Employee Performance Tracker (MySQL + Python + Power BI)

## Prerequisites
- MySQL Server and MySQL Workbench
- Python 3.10+
- Create or know MySQL credentials and grant rights to create database/table

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set environment variables (or edit the scripts):
```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=employee_performance_db
```

## Phase 1: Data & Database
1) Generate mock data, save Excel, create DB/table, import into MySQL, and run sample queries:
```bash
python 01_generate_and_import_mysql.py
```
Outputs:
- `data/employee_performance.xlsx`
- Table: `employee_performance_db.employees`

Use in MySQL Workbench (top KPI):
```sql
SELECT employee_id, name, department, kpi_score, attendance_percent
FROM employees
ORDER BY kpi_score DESC, attendance_percent DESC
LIMIT 5;
```

## Phase 2: Python Processing & Visualization
2) Analyze, clean, calculate, and create charts; export cleaned CSV and PNGs:
```bash
python 02_analyze_visualize_export.py
```
Outputs:
- `outputs/cleaned_employee_performance.csv`
- `outputs/avg_kpi_by_department.png`
- `outputs/avg_kpi_by_department_plotly.png`
- `outputs/attendance_category_distribution.png`
- `outputs/attendance_category_distribution_plotly.png`

## Phase 3: Power BI
3) Open Power BI Desktop and import `outputs/cleaned_employee_performance.csv`.
- Create a clustered bar: Axis = `department`, Value = `Average of kpi_score`.
- Create a pie: Legend = `attendance_category`, Values = `Count of employee_id`.
- Add a slicer: Field = `department`.

## Notes
- Rerunning `01_generate_and_import_mysql.py` will upsert rows via `REPLACE`.
- Adjust number of generated employees with `NUM_EMPLOYEES` env var (default 50).
- Plotly PNG export uses `kaleido`.
