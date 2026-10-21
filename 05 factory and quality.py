"""
05_factory_and_quality.py
Question: where do production orders lose time, and how big is the quality problem?
"""
import pandas as pd
from utils import load, title

# ------------------------------------------------------------
# 1) Late orders
# ------------------------------------------------------------
title("1) Production orders")
orders = load("Production_Orders")
orders["is_late"] = orders["Delay_Days"] > 0

print("Orders:", len(orders))
print("Late orders (%):", round(orders["is_late"].mean() * 100, 1))
late = orders[orders["is_late"]]
print("Average delay of a late order (days):", round(late["Delay_Days"].mean(), 1))

# ------------------------------------------------------------
# 2) Which stage is the bottleneck?
# ------------------------------------------------------------
title("2) Bottleneck of the late orders")
stages = late.groupby("Primary_Bottleneck")["Delay_Days"].agg(["size", "mean", "sum"])
stages.columns = ["late_orders", "avg_delay_days", "total_delay_days"]
print(stages.sort_values("total_delay_days", ascending=False).round(1))

# ------------------------------------------------------------
# 3) Machine downtime
# ------------------------------------------------------------
title("3) Machine downtime")
downtime = load("Machine_Downtime")
print("Total downtime hours:", round(downtime["Downtime_Hours"].sum()))
unplanned = downtime[downtime["Planned"] == "No"]["Downtime_Hours"].sum()
print("Unplanned share (%):", round(unplanned / downtime["Downtime_Hours"].sum() * 100, 1))
print("\nBy area (hours):")
print(downtime.groupby("Business_Area")["Downtime_Hours"].sum().sort_values(ascending=False).round(0))

# ------------------------------------------------------------
# 4) Printing yield and rework
# ------------------------------------------------------------
title("4) Printing batches")
batches = load("Printing_Batches")
print("Yield (%):", round(batches["Good_Qty"].sum() / batches["Printed_Qty"].sum() * 100, 2))
print("Rework cost (EGP):", round(batches["Rework_Cost_EGP"].sum()))

# ------------------------------------------------------------
# 5) Quality control
# ------------------------------------------------------------
title("5) Quality inspection")
quality = load("Quality")
per_stage = quality.groupby("Stage").agg(
    inspected=("Inspected_Qty", "sum"),
    rejected=("Rejected_Qty", "sum"),
    loss_egp=("Estimated_Loss_EGP", "sum"),
)
per_stage["reject_rate_%"] = per_stage["rejected"] / per_stage["inspected"] * 100
print(per_stage.round(2))
total_rate = quality["Rejected_Qty"].sum() / quality["Inspected_Qty"].sum() * 100
print("\nOverall reject rate (%):", round(total_rate, 2))

title("What this tells us")
print("Delays come from the production stages (sewing first), not from quality.")
print("The reject rate is almost the same at every stage, so it does not point to one problem.")
