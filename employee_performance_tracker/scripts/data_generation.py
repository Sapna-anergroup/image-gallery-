from pathlib import Path
import numpy as np
import pandas as pd


def generate_mock_employee_data(num_employees: int = 200, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    departments = ["Sales", "Engineering", "HR", "Marketing", "Finance", "Operations", "Support"]
    department_probs = np.array([0.18, 0.32, 0.06, 0.12, 0.10, 0.14, 0.08])

    first_names = [
        "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Cameron", "Avery",
        "Jamie", "Drew", "Quinn", "Rowan", "Hayden", "Reese", "Blake", "Parker",
        "Logan", "Skyler", "Elliot", "Sawyer",
    ]
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    ]

    employee_ids = [f"E{idx:04d}" for idx in range(1, num_employees + 1)]
    names = [f"{rng.choice(first_names)} {rng.choice(last_names)}" for _ in range(num_employees)]

    assigned_departments = rng.choice(departments, size=num_employees, p=department_probs)
    kpi_scores = np.clip(rng.normal(loc=75, scale=10, size=num_employees), 40, 100)
    attendance = 60 + 40 * rng.beta(a=5, b=2, size=num_employees)

    days_back = rng.integers(low=0, high=365, size=num_employees)
    last_training = pd.Timestamp.today().normalize() - pd.to_timedelta(days_back, unit="D")

    df = pd.DataFrame(
        {
            "Employee ID": employee_ids,
            "Name": names,
            "Department": assigned_departments,
            "KPI score": np.round(kpi_scores, 2),
            "Attendance %": np.round(attendance, 1),
            "Last Training Date": last_training,
        }
    )
    return df


def save_to_excel(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Employees", index=False)