"""
02_forecast.py
Question: how many units will we sell in Oct, Nov, Dec 2026?

Idea:
  - We have 36 months of sold units for every product in every location (177 series).
  - For each month we build "features": what was sold 1, 2, 3 and 12 months ago,
    the average of the last months, and the calendar (Ramadan, Eid, back to school, white friday).
  - A Gradient Boosting model learns the pattern.
  - To forecast 3 months we predict one month, add it to the history, then predict the next one.

Before trusting the model we TEST it:
  train on the data until June 2026, predict Jul-Aug-Sep 2026 (we know the answer),
  and compare with two simple guesses.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from utils import load, title, OUT_DIR

# ------------------------------------------------------------
# 1) Prepare the data: one row per (location, product), one column per month
# ------------------------------------------------------------
inventory = load("Inventory_History")
locations = load("Locations")[["Location_ID", "Channel"]]
products = load("Product_Master")[["Product_ID", "Product_Family", "Public_Retail_Price_EGP"]]
inventory = inventory.merge(locations, on="Location_ID").merge(products, on="Product_ID")

months = pd.period_range("2023-10", "2026-09", freq="M")          # 36 months
month_number = {str(m): i for i, m in enumerate(months)}
inventory["t"] = inventory["Snapshot_Month"].str[:7].map(month_number)
inventory["key"] = inventory["Location_ID"] + "|" + inventory["Product_ID"]

sold = inventory.pivot(index="key", columns="t", values="Sold_Qty")
keys = list(sold.index)
history = sold.values.astype(float)            # shape: 177 series x 36 months
n_series = len(keys)

info = inventory.drop_duplicates("key").set_index("key").loc[keys]
channel_code = info["Channel"].map({"Retail": 0, "Online": 1, "Wholesale": 2}).values
price = info["Public_Retail_Price_EGP"].values
family_code = pd.factorize(info["Product_Family"])[0]

# ------------------------------------------------------------
# 2) Calendar features for each month (36 months + 3 future months)
# ------------------------------------------------------------
all_months = pd.period_range("2023-10", "2026-12", freq="M")

ramadan = [("2024-03-11", "2024-04-09"), ("2025-03-01", "2025-03-30"), ("2026-02-18", "2026-03-19")]
eid_fitr = {"2024-04", "2025-03", "2026-03"}
eid_adha = {"2024-06", "2025-06", "2026-05"}


def ramadan_share(period):
    """What part of the month is inside Ramadan? (0 to 1)"""
    start, end = period.start_time, period.end_time
    days = 0
    for r_start, r_end in ramadan:
        a = max(pd.Timestamp(r_start), start)
        b = min(pd.Timestamp(r_end), end)
        if b >= a:
            days += (b - a).days + 1
    return days / period.days_in_month


calendar = pd.DataFrame({
    "month_of_year": [p.month for p in all_months],
    "ramadan": [ramadan_share(p) for p in all_months],
    "eid_fitr": [int(str(p) in eid_fitr) for p in all_months],
    "eid_adha": [int(str(p) in eid_adha) for p in all_months],
    "back_to_school": [int(p.month in (9, 10)) for p in all_months],
    "white_friday": [int(p.month == 11) for p in all_months],
})


# ------------------------------------------------------------
# 3) Features for one month t
# ------------------------------------------------------------
def make_features(data, t, scale):
    """data: units per series (rows) and month (columns). Returns one row per series."""
    cal = calendar.iloc[t]
    return np.column_stack([
        data[:, t - 1] / scale,                       # sold last month
        data[:, t - 2] / scale,                       # 2 months ago
        data[:, t - 3] / scale,                       # 3 months ago
        data[:, t - 12] / scale,                      # same month last year
        data[:, t - 3:t].mean(axis=1) / scale,        # average of last 3 months
        data[:, max(0, t - 12):t].mean(axis=1) / scale,   # average of last 12 months
        np.full(n_series, cal["month_of_year"]),
        np.full(n_series, cal["ramadan"]),
        np.full(n_series, cal["eid_fitr"]),
        np.full(n_series, cal["eid_adha"]),
        np.full(n_series, cal["back_to_school"]),
        np.full(n_series, cal["white_friday"]),
        np.full(n_series, t),
        channel_code,
        price,
        family_code,
    ])


def forecast(known, n_known, n_ahead):
    """Train on the first n_known months and predict the next n_ahead months."""
    # scale = average monthly units of each series, so big and small products are comparable
    scale = known.mean(axis=1).clip(min=1)
    data = np.hstack([known, np.zeros((n_series, n_ahead))])

    # build the training table: every month from 12 to n_known
    X_list, y_list = [], []
    for t in range(12, n_known):
        X_list.append(make_features(data, t, scale))
        y_list.append(data[:, t] / scale)
    X = np.vstack(X_list)
    y = np.concatenate(y_list)

    model = HistGradientBoostingRegressor(
        max_iter=250, learning_rate=0.05, max_depth=4,
        min_samples_leaf=30, l2_regularization=1.0, random_state=7,
    )
    model.fit(X, np.log1p(y))          # log makes big values less dominant

    # predict month by month, each prediction becomes history for the next one
    for step in range(n_ahead):
        t = n_known + step
        prediction = np.expm1(model.predict(make_features(data, t, scale)))
        data[:, t] = prediction.clip(min=0) * scale
    return data[:, n_known:]


def wape(actual, predicted):
    """Weighted absolute percentage error. Lower is better."""
    return np.abs(actual - predicted).sum() / actual.sum() * 100


# ------------------------------------------------------------
# 4) Test the model on months we already know (Jul, Aug, Sep 2026)
# ------------------------------------------------------------
title("Backtest: train until Jun-2026, predict Jul-Sep 2026")
n_train = 33
predicted = forecast(history[:, :n_train], n_train, 3)
actual = history[:, n_train:]

same_month_last_year = history[:, n_train - 12:n_train - 12 + 3]             # simple guess 1
mean_last_3 = np.repeat(history[:, n_train - 3:n_train].mean(axis=1, keepdims=True), 3, axis=1)  # simple guess 2

print("Error per product (WAPE %):")
print("  our model          :", round(wape(actual, predicted), 1))
print("  same month last yr :", round(wape(actual, same_month_last_year), 1))
print("  average last 3 mo  :", round(wape(actual, mean_last_3), 1))

print("\nError of the channel total (what a manager looks at):")
for name, code in [("Retail", 0), ("Online", 1), ("Wholesale", 2)]:
    rows = channel_code == code
    a = actual[rows].sum(axis=0)
    p = predicted[rows].sum(axis=0)
    print(f"  {name:10s}", round(np.abs(a - p).sum() / a.sum() * 100, 1), "%")

# ------------------------------------------------------------
# 5) The real forecast: Oct, Nov, Dec 2026
# ------------------------------------------------------------
title("Forecast Oct-Dec 2026")
future = forecast(history, 36, 3)
future_months = ["2026-10", "2026-11", "2026-12"]

out = pd.DataFrame(future, columns=future_months, index=keys)
out.index.name = "key"
out.to_csv(f"{OUT_DIR}/forecast_next_3_months.csv")

print("Total units forecast:", [int(x) for x in future.sum(axis=0)])
print("Same months last year:", [int(history[:, 24 + i].sum()) for i in range(3)])
print("Saved to outputs/forecast_next_3_months.csv")
