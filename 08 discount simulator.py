"""
08_discount_simulator.py  (the "Margin Guard")
Question: what if we do not allow wholesale discounts above a cap (for example 30%)?

Logic, for FY2026 wholesale only:
  - Every line with discount <= cap stays exactly the same.
  - Every line with discount > cap now gets the cap discount instead,
    but we assume only part of the volume stays (volume_kept, example 70%).
  - We compare the new gross profit with the old one.

Change CAP and VOLUME_KEPT below and run again.
"""
import pandas as pd
from utils import load_sales, title

CAP = 30            # maximum discount allowed (%)
VOLUME_KEPT = 0.70  # share of the volume we keep on lines that lose the extra discount

sales = load_sales()
wholesale = sales[(sales["Channel"] == "Wholesale") & (sales["FY"] == 2026)].copy()
wholesale["discount_pct"] = (wholesale["Discount_Pct"] * 100).round().astype(int)

# group lines by discount level to keep the calculation simple
levels = wholesale.groupby("discount_pct").agg(
    gross=("Gross_Sales_EGP", "sum"),     # sales before discount
    cogs=("Estimated_COGS_EGP", "sum"),   # cost of goods
).reset_index()


def simulate(cap, volume_kept):
    old_profit = 0
    new_profit = 0
    profit_per_full_volume = 0      # profit if we kept 100% of the capped lines
    old_profit_of_capped = 0
    for _, row in levels.iterrows():
        old_net = row["gross"] * (1 - row["discount_pct"] / 100)
        old_gp = old_net - row["cogs"]
        old_profit += old_gp

        if row["discount_pct"] > cap:
            kept_gross = row["gross"] * volume_kept
            kept_cogs = row["cogs"] * volume_kept
            new_net = kept_gross * (1 - cap / 100)
            new_profit += new_net - kept_cogs
            profit_per_full_volume += row["gross"] * (1 - cap / 100) - row["cogs"]
            old_profit_of_capped += old_gp
        else:
            new_profit += old_gp

    # break-even: the share of volume we must keep so that we do not lose money
    break_even = old_profit_of_capped / profit_per_full_volume if profit_per_full_volume > 0 else None
    return old_profit, new_profit, break_even


old_profit, new_profit, break_even = simulate(CAP, VOLUME_KEPT)

title(f"Cap = {CAP}%   Volume kept = {VOLUME_KEPT * 100:.0f}%")
print("Gross profit now (EGP)    :", round(old_profit))
print("Gross profit with cap (EGP):", round(new_profit))
print("Change per year (EGP)     :", round(new_profit - old_profit))
total_profit_all_channels = sales[sales["FY"] == 2026]["Gross_Profit_EGP"].sum()
print("Change in wholesale profit (%)       :", round((new_profit / old_profit - 1) * 100, 1))
print("Change in TOTAL company profit (%)   :", round((new_profit - old_profit) / total_profit_all_channels * 100, 1))
print("Break-even volume kept    :", round(break_even * 100), "%")

title("Try other values")
for cap in [25, 30, 35]:
    for kept in [0.5, 0.7, 0.9]:
        o, n, _ = simulate(cap, kept)
        print(f"cap {cap}%  volume kept {kept * 100:.0f}%  ->  {round((n - o) / 1e6, 2)} M EGP")

title("What this tells us")
print("Even if we lose 30% of the volume on those lines, profit still goes up.")
print("It stays positive down to the break-even volume. This is an ESTIMATE:")
print("test it on one customer tier for 30 days before using it everywhere.")
