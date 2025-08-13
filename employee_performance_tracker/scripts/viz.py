from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def plot_avg_kpi_by_dept(avg_df: pd.DataFrame, out_path: Path) -> None:
    plt.figure(figsize=(9, 5))
    bars = plt.bar(avg_df["department"], avg_df["kpi_score"], color="#4C78A8")
    plt.title("Average KPI by Department")
    plt.xlabel("Department")
    plt.ylabel("Average KPI")
    plt.xticks(rotation=30, ha="right")
    for b in bars:
        h = b.get_height()
        plt.annotate(f"{h:.1f}", (b.get_x() + b.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha="center")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_attendance_pie(dist_df: pd.DataFrame, out_path: Path) -> None:
    plt.figure(figsize=(6.5, 6.5))
    plt.pie(dist_df["count"], labels=dist_df["category"], autopct="%1.1f%%", startangle=140)
    plt.title("Attendance Category Distribution")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()