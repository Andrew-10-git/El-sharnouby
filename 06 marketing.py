"""
06_marketing.py
Question: which marketing platform gives back the most money for every pound spent?

ROAS (return on ad spend) = attributed revenue / spend
   ROAS = 1  -> we got back exactly what we spent
   ROAS < 1  -> we lost money
"""
import pandas as pd
from utils import load, load_sales, title

marketing = load("Marketing")
marketing["ROAS"] = marketing["Attributed_Revenue_EGP"] / marketing["Spend_EGP"]

# ------------------------------------------------------------
# 1) Per platform
# ------------------------------------------------------------
title("1) Return per platform")
platforms = marketing.groupby("Platform").agg(
    spend=("Spend_EGP", "sum"),
    revenue=("Attributed_Revenue_EGP", "sum"),
    campaigns=("Spend_EGP", "size"),
)
platforms["ROAS"] = platforms["revenue"] / platforms["spend"]
print(platforms.sort_values("ROAS", ascending=False).round(2))

# ------------------------------------------------------------
# 2) Campaigns that did not pay back
# ------------------------------------------------------------
title("2) Influencer campaigns")
influencers = marketing[marketing["Platform"] == "Influencer"]
print("Influencer campaigns:", len(influencers))
print("Campaigns with ROAS below 1:", int((influencers["ROAS"] < 1).sum()))
print("Influencer spend (EGP):", round(influencers["Spend_EGP"].sum()))

# ------------------------------------------------------------
# 3) Data check (very important before trusting the numbers)
# ------------------------------------------------------------
title("3) Data check")
sales = load_sales()
online_sales = sales[sales["Channel"] == "Online"]["Net_Sales_EGP"].sum()
attributed = marketing["Attributed_Revenue_EGP"].sum()
print("Revenue marketing claims (EGP):", round(attributed))
print("Real online sales (EGP)       :", round(online_sales))
print("Marketing claims", round(attributed / online_sales, 1), "times the real online sales!")
same = (marketing["Clicks"] == marketing["Landing_Page_Sessions"]).mean() * 100
print("Campaigns where clicks == sessions exactly (%):", round(same))

title("What this tells us")
print("Use the ROAS only to COMPARE platforms (WhatsApp and Google are far better than influencers).")
print("Do not use the absolute numbers, because attributed revenue is bigger than real sales.")
