import pandas as pd
import mysql.connector

# ====== EDIT THESE TO MATCH YOUR MYSQL WORKBENCH SETUP ======
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "your_password"
DB_NAME = "perfdb"
# ===========================================================

conn = mysql.connector.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
)
cur = conn.cursor()

# Top 5 by KPI
cur.execute(
    """
    SELECT employee_id, name, department, kpi_score
    FROM employee_performance
    ORDER BY kpi_score DESC
    LIMIT 5
    """
)
rows = cur.fetchall()
cols = [d[0] for d in cur.description]
print("\nTop 5 by KPI:")
print(pd.DataFrame(rows, columns=cols).to_string(index=False))

# Sales with KPI >= 85
cur.execute(
    """
    SELECT employee_id, name, kpi_score
    FROM employee_performance
    WHERE department = 'Sales' AND kpi_score >= 85
    ORDER BY kpi_score DESC
    """
)
rows = cur.fetchall()
cols = [d[0] for d in cur.description]
print("\nSales, KPI >= 85:")
print(pd.DataFrame(rows, columns=cols).to_string(index=False))

cur.close()
conn.close()