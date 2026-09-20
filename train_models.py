import os
import joblib
import pandas as pd

from utils.feature_engineering import create_features
from utils.ml_models import (
    train_delay_model,
    train_delivery_model
)
from sklearn.ensemble import IsolationForest


# =========================================================
# PATHS
# =========================================================

DATA_PATH = "data/raw/shipments.csv"

MODEL_DIR = "models"

DELAY_MODEL_PATH = os.path.join(
    MODEL_DIR,
    "delay_model.pkl"
)

DELIVERY_MODEL_PATH = os.path.join(
    MODEL_DIR,
    "delivery_model.pkl"
)

ANOMALY_MODEL_PATH = os.path.join(
    MODEL_DIR,
    "anomaly_model.pkl"
)


# =========================================================
# CREATE MODEL DIRECTORY
# =========================================================

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)


# =========================================================
# LOAD DATA
# =========================================================

print("Loading dataset...")

df = pd.read_csv(DATA_PATH)

print(f"Rows: {len(df)}")

print("\nColumns:")
print(df.columns.tolist())


# =========================================================
# CLEANING
# =========================================================

print("\nCleaning data...")

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# Remove duplicate rows
df = df.drop_duplicates()

# Numeric columns
numeric_columns = [
    "weight",
    "distance",
    "shipping_cost",
    "promised_delivery_days",
    "actual_delivery_days",
    "is_delayed"
]

for col in numeric_columns:

    if col in df.columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )


# =========================================================
# FEATURE ENGINEERING
# =========================================================

print("\nCreating features...")

df = create_features(df)


# =========================================================
# TRAIN DELAY MODEL
# =========================================================

print("\n==============================")
print("Training delay model...")
print("==============================")

train_delay_model(
    df,
    DELAY_MODEL_PATH
)


# =========================================================
# TRAIN DELIVERY TIME MODEL
# =========================================================

print("\n==============================")
print("Training delivery model...")
print("==============================")

train_delivery_model(
    df,
    DELIVERY_MODEL_PATH
)


# =========================================================
# ANOMALY DETECTION
# =========================================================

print("\n==============================")
print("Training anomaly model...")
print("==============================")


anomaly_features = [
    "weight",
    "distance",
    "shipping_cost",
    "promised_delivery_days",
    "actual_delivery_days",
    "delivery_delay_days"
]


available_anomaly_features = [
    col
    for col in anomaly_features
    if col in df.columns
]


anomaly_df = df[
    available_anomaly_features
].copy()


# Fill missing values
anomaly_df = anomaly_df.fillna(
    anomaly_df.median(numeric_only=True)
)


anomaly_model = IsolationForest(
    n_estimators=200,
    contamination=0.05,
    random_state=42
)


anomaly_model.fit(
    anomaly_df
)


joblib.dump(
    {
        "model": anomaly_model,
        "features": available_anomaly_features
    },
    ANOMALY_MODEL_PATH
)


print(
    f"Anomaly model saved to: {ANOMALY_MODEL_PATH}"
)


# =========================================================
# FINISHED
# =========================================================

print("\n")
print("========================================")
print("ALL MODELS TRAINED SUCCESSFULLY")
print("========================================")

print(
    f"Delay model:    {DELAY_MODEL_PATH}"
)

print(
    f"Delivery model: {DELIVERY_MODEL_PATH}"
)

print(
    f"Anomaly model:  {ANOMALY_MODEL_PATH}"
)