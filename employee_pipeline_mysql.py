import os
from datetime import date, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.types import Integer, String, Float, Date
import matplotlib.pyplot as plt
from dotenv import load_dotenv


load_dotenv()


def generate_mock_data(num_rows: int = 100, seed: int = 42) -> pd.DataFrame:
	"""Generate mock employee performance data."""
	rng = np.random.default_rng(seed)
	first_names = [
		"Alex", "Jamie", "Taylor", "Jordan", "Casey", "Riley", "Morgan", "Cameron", "Avery", "Parker",
		"Quinn", "Drew", "Rowan", "Elliot", "Emerson", "Hayden", "Kendall", "Logan", "Reese", "Skyler",
	]
	last_names = [
		"Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia", "Rodriguez", "Wilson",
		"Martinez", "Anderson", "Taylor", "Thomas", "Hernandez", "Moore", "Martin", "Lee", "Perez", "Thompson",
	]
	departments = [
		"Sales", "Marketing", "Engineering", "HR", "Finance", "Operations", "Support", "Product", "IT", "Customer Success",
	]

	employee_ids = np.arange(1001, 1001 + num_rows)
	names = []
	dept_values = []
	kpi_scores = []
	attendance_values = []
	training_dates = []

	today = date.today()
	start_date = today - timedelta(days=730)
	span_days = (today - start_date).days

	for _ in range(num_rows):
		name = f"{rng.choice(first_names)} {rng.choice(last_names)}"
		names.append(name)
		dept = rng.choice(departments)
		dept_values.append(dept)
		kpi = float(np.clip(rng.normal(75, 10), 40, 100))
		kpi_scores.append(round(kpi, 1))
		att = float(np.clip(rng.normal(90, 7), 60, 100))
		attendance_values.append(round(att, 1))
		offset_days = int(rng.integers(0, span_days + 1))
		training_dates.append(start_date + timedelta(days=offset_days))

	df = pd.DataFrame({
		"Employee ID": employee_ids,
		"Name": names,
		"Department": dept_values,
		"KPI score": kpi_scores,
		"Attendance %": attendance_values,
		"Last Training Date": training_dates,
	})
	return df


def get_mysql_engine() -> Engine:
	"""Create a SQLAlchemy engine for MySQL using env vars."""
	host = os.getenv("MYSQL_HOST", "127.0.0.1")
	port = int(os.getenv("MYSQL_PORT", "3306"))
	user = os.getenv("MYSQL_USER", "root")
	password = os.getenv("MYSQL_PASSWORD", "")
	database = os.getenv("MYSQL_DATABASE", "test")
	uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
	engine = create_engine(uri, pool_pre_ping=True)
	return engine


def write_to_mysql(df: pd.DataFrame, engine: Engine, table_name: str = "employee_performance") -> None:
	"""Write DataFrame to MySQL, replacing the table."""
	dtype = {
		"Employee ID": Integer(),
		"Name": String(100),
		"Department": String(50),
		"KPI score": Float(),
		"Attendance %": Float(),
		"Last Training Date": Date(),
	}
	df.to_sql(
		table_name,
		con=engine,
		if_exists="replace",
		index=False,
		dtype=dtype,
		method="multi",
		chunksize=1000,
	)


def top5_by_kpi(engine: Engine, table_name: str = "employee_performance") -> pd.DataFrame:
	query = text(
		f"SELECT `Employee ID`, `Name`, `Department`, `KPI score` "
		f"FROM `{table_name}` ORDER BY `KPI score` DESC LIMIT 5"
	)
	return pd.read_sql(query, engine)


def load_from_mysql(engine: Engine, table_name: str = "employee_performance") -> pd.DataFrame:
	query = text(
		f"SELECT `Employee ID`, `Name`, `Department`, `KPI score`, `Attendance %`, `Last Training Date` FROM `{table_name}`"
	)
	return pd.read_sql(query, engine, parse_dates=["Last Training Date"])


def clean_and_augment(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
	"""Basic cleaning and derived fields; returns (clean_df, avg_by_dept)."""
	df_clean = df.copy()
	df_clean["Last Training Date"] = pd.to_datetime(df_clean["Last Training Date"], errors="coerce").dt.date
	df_clean["KPI score"] = pd.to_numeric(df_clean["KPI score"], errors="coerce")
	df_clean["Attendance %"] = pd.to_numeric(df_clean["Attendance %"], errors="coerce")
	df_clean = df_clean.dropna(subset=["KPI score", "Attendance %", "Department"]) 

	def categorize(att: float) -> str:
		if att >= 90:
			return "High"
		if att >= 75:
			return "Medium"
		return "Low"

	df_clean["Attendance Category"] = df_clean["Attendance %"].apply(categorize)
	avg_by_dept = (
		df_clean.groupby("Department", as_index=False)["KPI score"].mean()
		.rename(columns={"KPI score": "Average KPI"})
	)
	return df_clean, avg_by_dept


def plot_avg_kpi_by_department(avg_df: pd.DataFrame, out_path: str) -> None:
	plt.figure(figsize=(8, 5))
	bars = plt.bar(avg_df["Department"], avg_df["Average KPI"], color="#4C78A8")
	plt.ylabel("Average KPI")
	plt.title("Average KPI by Department")
	plt.xticks(rotation=30, ha="right")
	for bar in bars:
		height = bar.get_height()
		plt.text(bar.get_x() + bar.get_width() / 2, height + 0.5, f"{height:.1f}", ha="center", va="bottom", fontsize=9)
	plt.tight_layout()
	plt.savefig(out_path, dpi=150)
	plt.close()


def plot_attendance_category_pie(df: pd.DataFrame, out_path: str) -> None:
	counts = df["Attendance Category"].value_counts().reindex(["High", "Medium", "Low"]).fillna(0)
	labels = counts.index.tolist()
	sizes = counts.values
	colors = ["#2AA02A", "#FF7F0E", "#D62728"]
	plt.figure(figsize=(5, 5))
	plt.pie(
		sizes,
		labels=labels,
		autopct=lambda p: f"{p:.1f}%" if p > 0 else "",
		startangle=90,
		colors=colors,
	)
	plt.title("Attendance Category Distribution")
	plt.tight_layout()
	plt.savefig(out_path, dpi=150)
	plt.close()


def main() -> None:
	import argparse

	parser = argparse.ArgumentParser(description="Employee Performance Data Pipeline (MySQL + Pandas + Matplotlib)")
	parser.add_argument("--rows", type=int, default=100, help="Number of mock rows to generate")
	parser.add_argument("--table", type=str, default="employee_performance", help="Target MySQL table name")
	parser.add_argument("--out-dir", type=str, default=".", help="Base directory for outputs")
	args = parser.parse_args()

	base_dir = os.path.abspath(args.out_dir)
	data_dir = os.path.join(base_dir, "data")
	charts_dir = os.path.join(base_dir, "charts")
	os.makedirs(data_dir, exist_ok=True)
	os.makedirs(charts_dir, exist_ok=True)

	# Phase 1: Mock Excel + Import to MySQL + sample SQL query
	df = generate_mock_data(args.rows)
	excel_path = os.path.join(data_dir, "employee_performance.xlsx")
	df.to_excel(excel_path, index=False)
	print(f"Wrote mock Excel: {excel_path}")

	engine = get_mysql_engine()
	write_to_mysql(df, engine, args.table)
	print(f"Wrote {len(df)} rows to MySQL table `{args.table}`")

	top5 = top5_by_kpi(engine, args.table)
	print("Top 5 by KPI:")
	print(top5.to_string(index=False))

	# Phase 2: Load from SQL -> clean -> visualize -> save PNGs
	df_sql = load_from_mysql(engine, args.table)
	df_clean, avg_by_dept = clean_and_augment(df_sql)

	bar_path = os.path.join(charts_dir, "avg_kpi_by_department.png")
	pie_path = os.path.join(charts_dir, "attendance_category_pie.png")
	plot_avg_kpi_by_department(avg_by_dept, bar_path)
	plot_attendance_category_pie(df_clean, pie_path)
	print(f"Saved charts to {charts_dir}")

	# Phase 3: Export cleaned CSV for Power BI
	cleaned_csv_path = os.path.join(data_dir, "employee_performance_cleaned.csv")
	df_clean.to_csv(cleaned_csv_path, index=False)
	print(f"Wrote cleaned CSV: {cleaned_csv_path}")


if __name__ == "__main__":
	main()