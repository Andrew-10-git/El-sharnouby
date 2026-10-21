"""
07_suppliers_procurement.py
Question: which suppliers deliver late, are prices going up, and does the spend make sense?
"""
import pandas as pd
from utils import load, load_sales, title

orders = load("Purchase_Orders", parse_dates=["Order_Date", "Promised_Date", "Actual_Receipt_Date"])
orders["delay_days"] = (orders["Actual_Receipt_Date"] - orders["Promised_Date"]).dt.days
orders["on_time"] = orders["delay_days"] <= 0
orders["spend"] = orders["Ordered_Qty"] * orders["Unit_Cost_EGP"]

# ------------------------------------------------------------
# 1) On-time delivery
# ------------------------------------------------------------
title("1) On-time delivery")
print("All purchase orders:", len(orders))
print("On-time (%):", round(orders["on_time"].mean() * 100, 1))

suppliers = orders.groupby("Supplier_ID").agg(
    orders=("PO_ID", "size"),
    on_time_pct=("on_time", lambda x: x.mean() * 100),
    spend=("spend", "sum"),
)
suppliers = suppliers.sort_values("on_time_pct")
print("\nWorst suppliers:")
print(suppliers.head(4).round(1))
bad = suppliers[suppliers["on_time_pct"] < 40]
print("\nSuppliers under 40% on time:", list(bad.index), "- spend with them (EGP):", round(bad["spend"].sum()))

# ------------------------------------------------------------
# 2) Material prices: FY2024 vs FY2026
# ------------------------------------------------------------
title("2) Price trend")
orders["FY"] = orders["Order_Date"].dt.year
orders.loc[orders["Order_Date"].dt.month >= 10, "FY"] += 1
price = orders.groupby(["Material_ID", "FY"])["Unit_Cost_EGP"].mean().unstack()
change = (price[2026] / price[2024] - 1) * 100            # % change per material
weight = orders.groupby("Material_ID")["spend"].sum()      # materials with more spend count more
print("Average price change (weighted by spend, %):", round((change * weight).sum() / weight.sum(), 1))

# ------------------------------------------------------------
# 3) Does the spend make sense? Compare with what the recipes (BOM) need
# ------------------------------------------------------------
title("3) Spend vs recipes (BOM)")
bom = load("Product_BOM")
sales = load_sales()
units_sold = sales.groupby("Product_ID")["Quantity"].sum()

bom = bom.merge(units_sold.rename("units_sold"), left_on="Product_ID", right_index=True)
bom["needed_qty"] = bom["Required_Per_Unit"] * bom["units_sold"]
needed = bom.groupby("Material_ID")["needed_qty"].sum()
avg_cost = orders.groupby("Material_ID")["Unit_Cost_EGP"].mean()

print("Purchase orders spend (EGP):", round(orders["spend"].sum()))
print("Value of materials needed for the units sold (EGP):", round((needed * avg_cost).sum()))

title("What this tells us")
print("Two suppliers are late most of the time and prices went up.")
print("The purchase spend is MUCH bigger than what the recipes need -> reconcile before acting.")
