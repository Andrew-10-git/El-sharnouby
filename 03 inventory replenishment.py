"""
03_inventory_replenishment.py
Question: what should we order, and where do we have too much stock?

Needs: run 02_forecast.py first (it creates outputs/forecast_next_3_months.csv).

For every product in every location:
  daily_demand   = forecast units for Oct-Dec / 92 days
  safety_stock   = 1.65 * (std of monthly sales / sqrt(30)) * sqrt(lead_time)
                   (1.65 means we accept to run out only 5% of the time)
  reorder_point  = daily_demand * lead_time + safety_stock
  order_quantity = daily_demand * (lead_time + 30 days) + safety_stock - stock_now
  excess         = stock above 90 days of demand (and above 180 days)
"""
import numpy as np
import pandas as pd
from utils import load, title, OUT_DIR

inventory = load("Inventory_History")
locations = load("Locations")[["Location_ID", "Channel"]]
products = load("Product_Master")[["Product_ID", "Public_Retail_Price_EGP"]]
inventory = inventory.merge(locations, on="Location_ID").merge(products, on="Product_ID")
inventory["key"] = inventory["Location_ID"] + "|" + inventory["Product_ID"]

forecast = pd.read_csv(f"{OUT_DIR}/forecast_next_3_months.csv", index_col="key")

# last month of data = current stock
last_month = inventory["Snapshot_Month"].max()
now = inventory[inventory["Snapshot_Month"] == last_month].set_index("key")
lead_time = inventory.groupby("key")["Supplier_Lead_Time_Days"].last()

rows = []
for key in forecast.index:
    # monthly sales of the last 12 months for this product/location
    monthly = inventory[inventory["key"] == key].sort_values("Snapshot_Month")["Sold_Qty"].values[-12:]
    daily_demand = forecast.loc[key].sum() / 92
    days = float(lead_time[key])

    safety_stock = 1.65 * (monthly.std() / np.sqrt(30)) * np.sqrt(days)
    reorder_point = daily_demand * days + safety_stock
    stock = float(now.loc[key, "Closing_Stock"])
    order_qty = max(0, daily_demand * (days + 30) + safety_stock - stock)
    keep = max(daily_demand * 90 + safety_stock, daily_demand * 180)
    excess = max(0, stock - keep)

    rows.append({
        "key": key,
        "channel": now.loc[key, "Channel"],
        "product": now.loc[key, "Product_Name"],
        "stock": stock,
        "daily_demand": daily_demand,
        "lead_time_days": days,
        "reorder_point": reorder_point,
        "old_reorder_point": float(now.loc[key, "Reorder_Point_Units"]),
        "order_qty": order_qty,
        "excess_units": excess,
        # we do not have the real cost, so we estimate it as 60% of the retail price
        "excess_value_egp": excess * float(now.loc[key, "Public_Retail_Price_EGP"]) * 0.6,
    })

result = pd.DataFrame(rows)
result.to_csv(f"{OUT_DIR}/replenishment_plan.csv", index=False)

# ------------------------------------------------------------
# Results
# ------------------------------------------------------------
title("Wholesale: what to order")
wholesale = result[result["channel"] == "Wholesale"]
below_new = (wholesale["stock"] < wholesale["reorder_point"]).sum()
below_old = (wholesale["stock"] < wholesale["old_reorder_point"]).sum()
print("Wholesale products:", len(wholesale))
print("Below the OLD reorder point :", below_old)
print("Below the NEW reorder point :", below_new)
print("Units to order now          :", round(wholesale["order_qty"].sum()))
print("\nTop 5 products to order:")
print(wholesale.sort_values("order_qty", ascending=False)[["product", "stock", "order_qty"]].head(5).round(0))

title("Retail + Online: too much stock")
others = result[result["channel"] != "Wholesale"]
print("Excess units:", round(others["excess_units"].sum()))
print("Excess value at estimated cost, 60% of price (EGP):", round(others["excess_value_egp"].sum()))

title("Stockout days in wholesale, by fiscal year")
inventory["FY"] = inventory["Snapshot_Month"].str[:4].astype(int)
inventory.loc[inventory["Snapshot_Month"].str[5:7].astype(int) >= 10, "FY"] += 1
w = inventory[inventory["Channel"] == "Wholesale"]
print(w.groupby("FY")["Stockout_Days_In_Month"].mean().round(2))
