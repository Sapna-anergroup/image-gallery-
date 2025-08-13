import pandas as pd
import mysql.connector

# ====== EDIT THESE TO MATCH YOUR MYSQL WORKBENCH SETUP ======
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"            # e.g., "root" or your user
DB_PASSWORD = "your_password"  # replace with your password
DB_NAME = "perfdb"
EXCEL_FILE = "employee_performance.xlsx"
# ===========================================================

# 1) Read Excel
print("Reading Excel ...")
df = pd.read_excel(EXCEL_FILE)

# 2) Rename columns for SQL
print("Preparing data ...")
df = df.rename(columns={
    "Employee ID": "employee_id",
    "Name": "name",
    "Department": "department",
    "KPI score": "kpi_score",
    "Attendance %": "attendance_pct",
    "Last Training Date": "last_training_date",
})

# Ensure types
df["kpi_score"] = pd.to_numeric(df["kpi_score"], errors="coerce")
df["attendance_pct"] = pd.to_numeric(df["attendance_pct"], errors="coerce")
df["last_training_date"] = pd.to_datetime(df["last_training_date"], errors="coerce").dt.date

# 3) Connect to MySQL (server level)
print("Connecting to MySQL ...")
conn = mysql.connector.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
)
conn.autocommit = True
cur = conn.cursor()

# 4) Create DB and table
print("Creating database/table if needed ...")
cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
cur.execute(f"USE {DB_NAME}")
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS employee_performance (
        employee_id VARCHAR(10) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        department VARCHAR(50) NOT NULL,
        kpi_score INT,
        attendance_pct DECIMAL(5,2),
        last_training_date DATE
    )
    """
)

# 5) Replace data (truncate + insert)
print("Replacing data ...")
cur.execute("TRUNCATE TABLE employee_performance")
insert_sql = (
    "INSERT INTO employee_performance "
    "(employee_id, name, department, kpi_score, attendance_pct, last_training_date) "
    "VALUES (%s, %s, %s, %s, %s, %s)"
)

ordered_cols = [
    "employee_id", "name", "department", "kpi_score", "attendance_pct", "last_training_date"
]
rows = list(df[ordered_cols].itertuples(index=False, name=None))
cur.executemany(insert_sql, rows)
conn.commit()

print(f"Imported {len(rows)} rows into {DB_NAME}.employee_performance")
cur.close()
conn.close()