# Employee Performance Mini-Pipeline (MySQL + Pandas + Matplotlib)

## 1) Setup
- Python 3.10+
- Create a virtual env and install deps:
  ```bash
  python -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  ```
- Copy `.env.example` to `.env` and set your MySQL credentials. Ensure the database exists (e.g., `hr_analytics`).
  ```sql
  -- In MySQL
  CREATE DATABASE IF NOT EXISTS hr_analytics;
  ```

## 2) Run (generates Excel, loads to MySQL, queries, visualizes, exports CSV)
```bash
python employee_pipeline_mysql.py --rows 200 --table employee_performance --out-dir .
```
Outputs:
- `data/employee_performance.xlsx`
- MySQL table `employee_performance`
- `charts/avg_kpi_by_department.png`
- `charts/attendance_category_pie.png`
- `data/employee_performance_cleaned.csv`

## 3) Example SQL queries
```sql
-- Top 5 employees by KPI
SELECT `Employee ID`, `Name`, `Department`, `KPI score`
FROM `employee_performance`
ORDER BY `KPI score` DESC
LIMIT 5;

-- Average KPI per department
SELECT `Department`, ROUND(AVG(`KPI score`), 2) AS `Average KPI`
FROM `employee_performance`
GROUP BY `Department`
ORDER BY `Average KPI` DESC;

-- Filtered results: Engineering with High attendance
SELECT *
FROM `employee_performance`
WHERE `Department` = 'Engineering' AND `Attendance %` >= 90
ORDER BY `KPI score` DESC;
```

## 4) Power BI (replicate charts)
- Get Data → Text/CSV → select `data/employee_performance_cleaned.csv`.
- Bar chart: Axis=`Department`, Values=`KPI score` (Average).
- Pie chart: Legend=`Attendance Category`, Values=`Attendance Category` (Count).
- Add a Slicer: Field=`Department`.

## Notes
- Credentials are read from `.env` via `python-dotenv`.
- If you prefer PostgreSQL, change the engine URL pattern to `postgresql+psycopg2://...` and install `psycopg2-binary`.
