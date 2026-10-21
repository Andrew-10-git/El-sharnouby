# El-Sharnouby Analysis (Python scripts)

Simple step-by-step scripts behind the dashboard. Each file answers one business question
and prints its results with a short conclusion at the end.

## How to run
1. Put all the CSV files in a folder called `data/` (Sales_Transactions can stay in its zip).
2. `pip install -r requirements.txt`
3. Run in this order (02 must run before 03):

| File | Question |
|------|----------|
| `01_sales_and_margin.py` | How much do we sell and earn? Where do discounts lose money? |
| `02_forecast.py` | How many units next quarter? (with a backtest) |
| `03_inventory_replenishment.py` | What to order, where is the excess stock? |
| `04_customers_rfm_churn.py` | RFM segments, who is at risk, can a model predict it? |
| `05_factory_and_quality.py` | Late orders, bottleneck, downtime, quality |
| `06_marketing.py` | Return on ad spend per platform + data check |
| `07_suppliers_procurement.py` | On-time suppliers, price trend, spend check |
| `08_discount_simulator.py` | Margin Guard: what if discounts are capped? |
| `09_branches.py` | Demand per governorate, next branch candidates |

`utils.py` has the shared helpers (load files, fiscal year starts in October).

## Notes
- The data is mostly modeled, not exported from a live system. Treat results as direction.
- The cost of excess stock is estimated as 60% of the retail price (no real cost in the data).
