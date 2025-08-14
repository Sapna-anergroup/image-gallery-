import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import mysql.connector
from mysql.connector import errorcode


# -----------------------------
# Configuration
# -----------------------------
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "employee_performance_db")

NUM_EMPLOYEES = int(os.getenv("NUM_EMPLOYEES", "50"))

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
EXCEL_PATH = DATA_DIR / "employee_performance.xlsx"

TABLE_NAME = "employees"


# -----------------------------
# Data generation
# -----------------------------

def generate_mock_employee_data(num_employees: int) -> pd.DataFrame:
	departments: List[str] = [
		"Sales",
		"Engineering",
		"HR",
		"Finance",
		"Marketing",
		"Support",
	]

	rows: List[Tuple] = []
	start_id = 1001
	for i in range(num_employees):
		employee_id = start_id + i
		name = f"Employee {i + 1:03d}"
		department = random.choice(departments)
		kpi_score = round(random.uniform(60, 100), 1)
		attendance_percent = round(random.uniform(70, 100), 1)
		last_training_date = (datetime.now() - timedelta(days=random.randint(0, 365)) ).date()

		rows.append(
			(
				employee_id,
				name,
				department,
				kpi_score,
				attendance_percent,
				last_training_date,
			)
		)

	df = pd.DataFrame(
		rows,
		columns=[
			"employee_id",
			"name",
			"department",
			"kpi_score",
			"attendance_percent",
			"last_training_date",
		],
	)
	return df


def save_dataframe_to_excel(df: pd.DataFrame, excel_path: Path) -> None:
	# Requires openpyxl installed
	df.to_excel(excel_path, index=False, sheet_name="Employees")


# -----------------------------
# MySQL helpers
# -----------------------------

def connect_mysql(database: str | None = None) -> mysql.connector.connection.MySQLConnection:
	connection = mysql.connector.connect(
		host=MYSQL_HOST,
		port=MYSQL_PORT,
		user=MYSQL_USER,
		password=MYSQL_PASSWORD,
		database=database,
	)
	return connection


def ensure_database_exists() -> None:
	conn = connect_mysql(database=None)
	conn.autocommit = True
	try:
		with conn.cursor() as cur:
			cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}`;")
	finally:
		conn.close()


def ensure_table_exists() -> None:
	conn = connect_mysql(database=MYSQL_DATABASE)
	try:
		with conn.cursor() as cur:
			cur.execute(
				f"""
				CREATE TABLE IF NOT EXISTS `{TABLE_NAME}` (
					`employee_id` INT PRIMARY KEY,
					`name` VARCHAR(100) NOT NULL,
					`department` VARCHAR(50) NOT NULL,
					`kpi_score` DECIMAL(5,2) NOT NULL,
					`attendance_percent` DECIMAL(5,2) NOT NULL,
					`last_training_date` DATE NOT NULL
				) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
				"""
			)
			conn.commit()
	finally:
		conn.close()


def import_dataframe_into_mysql(df: pd.DataFrame) -> None:
	# Use REPLACE to allow re-runs without duplicate key errors
	insert_sql = (
		f"""
		REPLACE INTO `{TABLE_NAME}`
			(`employee_id`, `name`, `department`, `kpi_score`, `attendance_percent`, `last_training_date`)
		VALUES (%s, %s, %s, %s, %s, %s);
		"""
	)

	records = [
		(
			int(row.employee_id),
			str(row.name),
			str(row.department),
			float(row.kpi_score),
			float(row.attendance_percent),
			pd.to_datetime(row.last_training_date).date(),
		)
		for row in df.itertuples(index=False)
	]

	conn = connect_mysql(database=MYSQL_DATABASE)
	try:
		with conn.cursor() as cur:
			cur.executemany(insert_sql, records)
			conn.commit()
	finally:
		conn.close()


def run_sample_queries() -> None:
	conn = connect_mysql(database=MYSQL_DATABASE)
	try:
		with conn.cursor(dictionary=True) as cur:
			cur.execute(f"SELECT COUNT(*) AS row_count FROM `{TABLE_NAME}`;")
			count = cur.fetchone()["row_count"]
			print(f"Rows in table `{TABLE_NAME}`: {count}")

			print("\nTop 5 employees by KPI:")
			sql = (
				f"SELECT employee_id, name, department, kpi_score, attendance_percent "
				f"FROM `{TABLE_NAME}` ORDER BY kpi_score DESC, attendance_percent DESC LIMIT 5;"
			)
			cur.execute(sql)
			for row in cur.fetchall():
				print(row)
	finally:
		conn.close()


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
	print("Generating mock employee data...")
	df = generate_mock_employee_data(NUM_EMPLOYEES)
	print(f"Generated {len(df)} rows.")

	print(f"Saving to Excel at: {EXCEL_PATH}")
	save_dataframe_to_excel(df, EXCEL_PATH)
	print("Excel file saved.")

	print("Ensuring MySQL database and table exist...")
	ensure_database_exists()
	ensure_table_exists()
	print("Database and table are ready.")

	print("Importing data into MySQL...")
	import_dataframe_into_mysql(df)
	print("Data import completed.")

	run_sample_queries()

	print("\nYou can also run this in MySQL Workbench:")
	print(
		f"""
	-- Connect to `{MYSQL_DATABASE}` and run:
	SELECT employee_id, name, department, kpi_score, attendance_percent
	FROM `{TABLE_NAME}`
	ORDER BY kpi_score DESC, attendance_percent DESC
	LIMIT 5;
	""".strip()
	)