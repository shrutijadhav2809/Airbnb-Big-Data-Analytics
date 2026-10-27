
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "advanced_results"
OUTPUT_DIR.mkdir(exist_ok=True)

# DEMONSTRATION ONLY:
# This synthetic dataset is not real Airbnb booking history.
# It demonstrates how a demand-forecasting pipeline works.
rng = np.random.default_rng(42)
days = pd.date_range("2025-01-01", periods=365, freq="D")

data = pd.DataFrame({"date": days})
data["day_of_week"] = data["date"].dt.dayofweek
data["month"] = data["date"].dt.month
data["is_weekend"] = (data["day_of_week"] >= 5).astype(int)

# Simulated demand pattern with weekly and seasonal effects.
seasonal = 20 * np.sin(2 * np.pi * data["date"].dt.dayofyear / 365)
weekend_effect = 15 * data["is_weekend"]
noise = rng.normal(0, 5, len(data))

data["simulated_demand"] = np.maximum(
    1,
    100 + seasonal + weekend_effect + noise
).round().astype(int)

features = ["day_of_week", "month", "is_weekend"]
X = data[features]
y = data["simulated_demand"]

# Chronological split: train on earlier days, test on later days.
split = int(len(data) * 0.8)
X_train, X_test = X.iloc[:split], X.iloc[split:]
y_train, y_test = y.iloc[:split], y.iloc[split:]

model = RandomForestRegressor(
    n_estimators=200,
    random_state=42,
)
model.fit(X_train, y_train)

predictions = np.maximum(0, model.predict(X_test)).round(1)

mae = mean_absolute_error(y_test, predictions)
rmse = np.sqrt(mean_squared_error(y_test, predictions))

results = data.iloc[split:].copy()
results["predicted_demand"] = predictions
results["actual_simulated_demand"] = y_test.to_numpy()

results.to_csv(
    OUTPUT_DIR / "demand_forecast_demo.csv",
    index=False,
)

metrics = pd.DataFrame([{
    "model": "Random Forest Regressor",
    "data_type": "Synthetic demonstration data",
    "training_days": len(X_train),
    "testing_days": len(X_test),
    "MAE": round(mae, 2),
    "RMSE": round(rmse, 2),
}])

metrics.to_csv(
    OUTPUT_DIR / "demand_forecast_metrics.csv",
    index=False,
)

print("Demand forecasting demonstration completed.")
print("IMPORTANT: Results use synthetic data, not actual Airbnb bookings.")
print(f"Training days: {len(X_train)}")
print(f"Testing days: {len(X_test)}")
print(f"MAE: {mae:.2f}")
print(f"RMSE: {rmse:.2f}")
print(f"Results saved in: {OUTPUT_DIR}")
