import pandas as pd
import matplotlib.pyplot as plt
import mysql.connector

# ====== EDIT THESE TO MATCH YOUR MYSQL WORKBENCH SETUP ======
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "your_password"
DB_NAME = "perfdb"
# ===========================================================

# 1) Load from MySQL
conn = mysql.connector.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
)
cur = conn.cursor()
cur.execute("SELECT employee_id, name, department, kpi_score, attendance_pct, last_training_date FROM employee_performance")
rows = cur.fetchall()
cols = [d[0] for d in cur.description]
cur.close()
conn.close()

df = pd.DataFrame(rows, columns=cols)

# 2) Basic cleaning
df["department"] = df["department"].astype(str).str.strip()
df["kpi_score"] = pd.to_numeric(df["kpi_score"], errors="coerce")
df["attendance_pct"] = pd.to_numeric(df["attendance_pct"], errors="coerce")

# 3) Calculations
avg_kpi = (
    df.groupby("department", as_index=False)["kpi_score"].mean().sort_values("kpi_score", ascending=False)
)

df["attendance_category"] = pd.cut(
    df["attendance_pct"],
    bins=[0, 80, 90, 100],
    labels=["Low", "Medium", "High"],
    include_lowest=True,
    right=True,
)

# 4) Visualization 1: Bar chart – Average KPI by department
plt.figure(figsize=(6, 4))
plt.bar(avg_kpi["department"], avg_kpi["kpi_score"], color="#4e79a7")
plt.ylabel("Average KPI")
plt.xlabel("Department")
plt.title("Average KPI by Department")
plt.tight_layout()
plt.savefig("avg_kpi_by_department.png", dpi=150)
plt.close()

# 5) Visualization 2: Pie chart – Attendance category distribution
counts = df["attendance_category"].value_counts().reindex(["High", "Medium", "Low"]).fillna(0)
plt.figure(figsize=(5, 5))
plt.pie(counts.values, labels=counts.index, autopct="%1.1f%%", startangle=90,
        colors=["#59a14f", "#f28e2b", "#e15759"])
plt.title("Attendance Category Distribution")
plt.tight_layout()
plt.savefig("attendance_category_distribution.png", dpi=150)
plt.close()

# 6) Save cleaned dataset
df.to_csv("employee_performance_cleaned.csv", index=False)

print("Saved: avg_kpi_by_department.png, attendance_category_distribution.png, employee_performance_cleaned.csv")