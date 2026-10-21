"""
utils.py - small helper functions used by all the scripts.

Put all the CSV files in the folder called "data" (next to these scripts).
Sales_Transactions.csv can stay inside its .zip file, we read it from there.
"""
import os
import zipfile
import pandas as pd

DATA_DIR = "data"
OUT_DIR = "outputs"
os.makedirs(OUT_DIR, exist_ok=True)


def load(name, **kwargs):
    """Read one CSV file by its name, example: load("Customers")"""
    path = os.path.join(DATA_DIR, name + ".csv")
    if os.path.exists(path):
        return pd.read_csv(path, **kwargs)

    # maybe the file is inside a zip (this is the case for the sales file)
    for file in os.listdir(DATA_DIR):
        if file.endswith(".zip") and name in file:
            with zipfile.ZipFile(os.path.join(DATA_DIR, file)) as z:
                inner = [n for n in z.namelist() if n.endswith(name + ".csv") and "__MACOSX" not in n][0]
                with z.open(inner) as f:
                    return pd.read_csv(f, **kwargs)
    raise FileNotFoundError("Could not find " + name + ".csv inside the data folder")


def load_sales():
    """Sales table with two extra columns: fiscal year (FY) and month (Month)"""
    sales = load("Sales_Transactions", parse_dates=["Order_Date"])
    # The fiscal year starts in October. Oct-2025 belongs to FY2026.
    sales["FY"] = sales["Order_Date"].dt.year
    sales.loc[sales["Order_Date"].dt.month >= 10, "FY"] += 1
    sales["Month"] = sales["Order_Date"].dt.to_period("M").astype(str)
    return sales


def pct(a, b):
    """a as a percentage of b"""
    return a / b * 100


def title(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)
