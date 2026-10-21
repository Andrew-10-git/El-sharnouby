"""
09_branches.py
Question: where is the demand, and where could the next branch open?

We have only ONE store (Alexandria). Cairo, Giza and others buy online
or through wholesale. We look at the retail + online customers (B2C) per governorate.
"""
import pandas as pd
from utils import load, load_sales, title

sales = load_sales()

title("1) Sales per governorate (all channels)")
by_gov = sales.groupby("Customer_Governorate")["Net_Sales_EGP"].sum().sort_values(ascending=False)
print(by_gov.head(8).round(0))

title("2) Retail + Online only (customers buying as consumers)")
b2c = sales[sales["Channel"] != "Wholesale"]
table = b2c.groupby("Customer_Governorate").agg(
    sales=("Net_Sales_EGP", "sum"),
    customers=("Customer_ID", "nunique"),
    orders=("Invoice_ID", "nunique"),
)
table["avg_order_value"] = table["sales"] / table["orders"]

# does the governorate already have a store?
locations = load("Locations")
store_gov = locations[locations["Location_Type"] == "Retail Store"]["Governorate"].unique()
table["has_store"] = table.index.isin(store_gov)
print(table.sort_values("sales", ascending=False).head(8).round(0))

title("3) Candidates for the next branch (demand but no store)")
candidates = table[~table["has_store"]].sort_values("sales", ascending=False).head(3)
print(candidates.round(0))

title("What this tells us")
print("We have one store (Alexandria). Cairo, Giza and Beheira have the most demand without a store.")
print("This is only a shortlist: rent and staff costs are not in the data.")
