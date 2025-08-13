import pandas as pd


data = {
    "Employee ID": [
        "E001", "E002", "E003", "E004", "E005", "E006",
        "E007", "E008", "E009", "E010", "E011", "E012"
    ],
    "Name": [
        "Alice", "Bob", "Charlie", "Diana", "Ethan", "Fiona",
        "George", "Hannah", "Ian", "Julia", "Kevin", "Lily"
    ],
    "Department": [
        "Sales", "Sales", "Finance", "Finance", "HR", "HR",
        "Engineering", "Engineering", "Engineering", "Sales", "Finance", "HR"
    ],
    "KPI score": [92, 85, 78, 88, 90, 73, 95, 67, 82, 91, 76, 84],
    "Attendance %": [96, 89, 92, 85, 88, 78, 99, 81, 90, 94, 87, 76],
    "Last Training Date": [
        "2024-11-03", "2024-09-12", "2024-07-21", "2024-08-18",
        "2024-10-05", "2024-03-29", "2024-12-01", "2024-02-14",
        "2024-06-30", "2024-05-25", "2024-04-17", "2024-01-22"
    ],
}


df = pd.DataFrame(data)
df.to_excel("employee_performance.xlsx", index=False)
print("Saved employee_performance.xlsx")