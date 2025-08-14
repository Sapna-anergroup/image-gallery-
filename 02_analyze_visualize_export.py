import os
from pathlib import Path

import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt
import plotly.express as px

# -----------------------------
# Configuration
# -----------------------------
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "employee_performance_db")
TABLE_NAME = "employees"

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PNG_BAR_PATH = OUTPUT_DIR / "avg_kpi_by_department.png"
PNG_PIE_PATH = OUTPUT_DIR / "attendance_category_distribution.png"
CLEAN_CSV_PATH = OUTPUT_DIR / "cleaned_employee_performance.csv"


# -----------------------------
# Helpers
# -----------------------------

def connect_mysql(database: str | None = None):
	return mysql.connector.connect(
		host=MYSQL_HOST,
		port=MYSQL_PORT,
		user=MYSQL_USER,
		password=MYSQL_PASSWORD,
		database=database,
	)


def load_employees_df() -> pd.DataFrame:
	conn = connect_mysql(database=MYSQL_DATABASE)
	try:
		df = pd.read_sql(
			f"SELECT employee_id, name, department, kpi_score, attendance_percent, last_training_date FROM `{TABLE_NAME}`;",
			con=conn,
		)
		return df
	finally:
		conn.close()


def clean_and_enrich(df: pd.DataFrame) -> pd.DataFrame:
	out = df.copy()
	# Convert types
	out["kpi_score"] = pd.to_numeric(out["kpi_score"], errors="coerce")
	out["attendance_percent"] = pd.to_numeric(out["attendance_percent"], errors="coerce")
	out["last_training_date"] = pd.to_datetime(out["last_training_date"], errors="coerce")

	# Drop rows with missing critical fields
	out = out.dropna(subset=["employee_id", "department", "kpi_score", "attendance_percent"])

	# Attendance category
	def categorize_attendance(pct: float) -> str:
		if pct >= 90:
			return "High"
		elif pct >= 80:
			return "Medium"
		return "Low"

	out["attendance_category"] = out["attendance_percent"].apply(categorize_attendance)
	return out


def plot_avg_kpi_by_department(df: pd.DataFrame, png_path: Path) -> None:
	avg = df.groupby("department", as_index=False)["kpi_score"].mean().sort_values("kpi_score", ascending=False)
	plt.figure(figsize=(8, 5))
	plt.bar(avg["department"], avg["kpi_score"], color="#4C78A8")
	plt.title("Average KPI by Department")
	plt.xlabel("Department")
	plt.ylabel("Average KPI")
	plt.xticks(rotation=30, ha="right")
	plt.tight_layout()
	plt.savefig(png_path, dpi=150)
	plt.close()

	# Also create an interactive Plotly version (optional)
	fig = px.bar(avg, x="department", y="kpi_score", title="Average KPI by Department (Interactive)")
	fig.write_image(str(png_path.with_name(png_path.stem + "_plotly.png")))


def plot_attendance_category_distribution(df: pd.DataFrame, png_path: Path) -> None:
	dist = df["attendance_category"].value_counts().reset_index()
	dist.columns = ["attendance_category", "count"]

	plt.figure(figsize=(6, 6))
	plt.pie(dist["count"], labels=dist["attendance_category"], autopct="%1.1f%%", startangle=140)
	plt.title("Attendance Category Distribution")
	plt.tight_layout()
	plt.savefig(png_path, dpi=150)
	plt.close()

	# Plotly version
	fig = px.pie(dist, names="attendance_category", values="count", title="Attendance Category Distribution (Interactive)")
	fig.write_image(str(png_path.with_name(png_path.stem + "_plotly.png")))


if __name__ == "__main__":
	print("Loading data from MySQL into pandas...")
	df = load_employees_df()
	print(f"Loaded {len(df)} rows.")

	print("Cleaning and enriching data...")
	clean_df = clean_and_enrich(df)
	print(f"Rows after cleaning: {len(clean_df)}")

	print(f"Saving cleaned CSV for Power BI at: {CLEAN_CSV_PATH}")
	clean_df.to_csv(CLEAN_CSV_PATH, index=False)
	print("CSV saved.")

	print(f"Generating bar chart to {PNG_BAR_PATH}")
	plot_avg_kpi_by_department(clean_df, PNG_BAR_PATH)
	print("Bar chart saved.")

	print(f"Generating pie chart to {PNG_PIE_PATH}")
	plot_attendance_category_distribution(clean_df, PNG_PIE_PATH)
	print("Pie chart saved.")