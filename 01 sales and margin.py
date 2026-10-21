"""
01_sales_and_margin.py
Question: how much do we sell, how much do we earn, and where is the money lost?

Steps:
  1. Sales and margin per fiscal year (FY starts in October)
  2. Sales and margin per channel (Wholesale / Online / Retail)
  3. Wholesale discounts: which discount levels lose money?
  4. Returns
"""
import pandas as pd
from utils import load_sales, pct, title

sales = load_sales()
print("Rows in sales table:", len(sales))

# ------------------------------------------------------------
# 1) Fiscal years
# ------------------------------------------------------------
title("1) Sales per fiscal year")
by_year = sales.groupby("FY").agg(
    net_sales=("Net_Sales_EGP", "sum"),
    gross_profit=("Gross_Profit_EGP", "sum"),
)
by_year["margin_%"] = pct(by_year["gross_profit"], by_year["net_sales"])
by_year["growth_%"] = by_year["net_sales"].pct_change() * 100
print(by_year.round(1))

# ------------------------------------------------------------
# 2) Channels (only the latest year, FY2026)
# ------------------------------------------------------------
title("2) Channels in FY2026")
last_year = sales[sales["FY"] == 2026]
by_channel = last_year.groupby("Channel").agg(
    net_sales=("Net_Sales_EGP", "sum"),
    gross_profit=("Gross_Profit_EGP", "sum"),
)
by_channel["margin_%"] = pct(by_channel["gross_profit"], by_channel["net_sales"])
by_channel["share_of_sales_%"] = pct(by_channel["net_sales"], by_channel["net_sales"].sum())
print(by_channel.round(1))

# growth of each channel compared with FY2025
prev_year = sales[sales["FY"] == 2025].groupby("Channel")["Net_Sales_EGP"].sum()
growth = (by_channel["net_sales"] / prev_year - 1) * 100
print("\nGrowth vs FY2025 (%):")
print(growth.round(1))

# ------------------------------------------------------------
# 3) Wholesale discounts
# ------------------------------------------------------------
title("3) Wholesale discounts")
wholesale = sales[sales["Channel"] == "Wholesale"].copy()

# put the discount in groups: 0-10%, 10-20% ...
wholesale["discount_band"] = pd.cut(
    wholesale["Discount_Pct"],
    bins=[-0.01, 0.10, 0.20, 0.30, 0.40],
    labels=["0-10%", "10-20%", "20-30%", "30-40%"],
)
bands = wholesale.groupby("discount_band").agg(
    net_sales=("Net_Sales_EGP", "sum"),
    gross_profit=("Gross_Profit_EGP", "sum"),
    lines=("Row_ID", "size"),
)
bands["margin_%"] = pct(bands["gross_profit"], bands["net_sales"])
print(bands.round(1))

# lines where we sold below cost (gross profit is negative)
loss_lines = wholesale[wholesale["Gross_Profit_EGP"] < 0]
print("\nLines sold at a loss:", len(loss_lines))
print("Total loss (EGP):", round(-loss_lines["Gross_Profit_EGP"].sum()))
print("Average discount on those lines (%):", round(loss_lines["Discount_Pct"].mean() * 100, 1))

# ------------------------------------------------------------
# 4) Returns
# ------------------------------------------------------------
title("4) Returns")
sales["is_returned"] = sales["Returned"] == "Yes"
returns = sales.groupby("Channel").agg(
    return_rate_pct=("is_returned", lambda x: x.mean() * 100),
    refunds_egp=("Refund_Value_EGP", "sum"),
)
print(returns.round(1))
print("\nMain return reasons (by refund value):")
reasons = sales[sales["is_returned"]].groupby("Return_Reason")["Refund_Value_EGP"].sum()
print(reasons.sort_values(ascending=False).round(0))

# ------------------------------------------------------------
# Conclusion
# ------------------------------------------------------------
title("What this tells us")
share = by_channel.loc["Wholesale", "share_of_sales_%"]
margin = by_channel.loc["Wholesale", "margin_%"]
print(f"Wholesale is {share:.0f}% of the sales but earns only {margin:.1f}% margin.")
print("So one pricing decision in wholesale moves the total profit.")
