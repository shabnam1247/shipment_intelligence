import pandas as pd
import numpy as np


def create_features(df):

    df = df.copy()

    # -------------------------------------------------
    # Convert shipment date
    # -------------------------------------------------
    if "shipment_date" in df.columns:
        df["shipment_date"] = pd.to_datetime(
            df["shipment_date"],
            errors="coerce"
        )

        df["shipment_year"] = df["shipment_date"].dt.year
        df["shipment_month"] = df["shipment_date"].dt.month
        df["shipment_day"] = df["shipment_date"].dt.day
        df["shipment_dayofweek"] = df["shipment_date"].dt.dayofweek

    # -------------------------------------------------
    # Create delivery delay
    # -------------------------------------------------
    if (
        "actual_delivery_days" in df.columns
        and "promised_delivery_days" in df.columns
    ):

        df["delivery_delay_days"] = (
            df["actual_delivery_days"]
            - df["promised_delivery_days"]
        )

        df["is_delayed"] = (
            df["delivery_delay_days"] > 0
        ).astype(int)

    # -------------------------------------------------
    # If is_delayed already exists, keep it
    # -------------------------------------------------
    elif "is_delayed" in df.columns:

        df["is_delayed"] = pd.to_numeric(
            df["is_delayed"],
            errors="coerce"
        ).fillna(0).astype(int)

    # -------------------------------------------------
    # Delivery status
    # -------------------------------------------------
    if "delivery_status" in df.columns:

        df["delivery_status"] = (
            df["delivery_status"]
            .astype(str)
            .str.strip()
        )

    # -------------------------------------------------
    # Distance per delivery day
    # -------------------------------------------------
    if (
        "distance" in df.columns
        and "actual_delivery_days" in df.columns
    ):

        df["distance_per_day"] = (
            df["distance"] /
            df["actual_delivery_days"].replace(0, np.nan)
        )

        df["distance_per_day"] = (
            df["distance_per_day"]
            .replace([np.inf, -np.inf], np.nan)
            .fillna(0)
        )

    # -------------------------------------------------
    # Cost per kg
    # -------------------------------------------------
    if (
        "shipping_cost" in df.columns
        and "weight" in df.columns
    ):

        df["cost_per_kg"] = (
            df["shipping_cost"] /
            df["weight"].replace(0, np.nan)
        )

        df["cost_per_kg"] = (
            df["cost_per_kg"]
            .replace([np.inf, -np.inf], np.nan)
            .fillna(0)
        )

    # -------------------------------------------------
    # Distance category
    # -------------------------------------------------
    if "distance" in df.columns:

        df["distance_category"] = pd.cut(
            df["distance"],
            bins=[0, 500, 1000, 2000, np.inf],
            labels=[
                "Short",
                "Medium",
                "Long",
                "Very Long"
            ]
        )

    # -------------------------------------------------
    # Weight category
    # -------------------------------------------------
    if "weight" in df.columns:

        df["weight_category"] = pd.cut(
            df["weight"],
            bins=[0, 5, 10, 20, np.inf],
            labels=[
                "Light",
                "Medium",
                "Heavy",
                "Very Heavy"
            ]
        )

    # -------------------------------------------------
    # Fill missing numerical values
    # -------------------------------------------------
    numeric_columns = df.select_dtypes(
        include=["int64", "float64", "int32", "float32"]
    ).columns

    for col in numeric_columns:
        df[col] = df[col].fillna(df[col].median())

    # -------------------------------------------------
    # Fill missing categorical values
    # -------------------------------------------------
    categorical_columns = df.select_dtypes(
        include=["object", "category"]
    ).columns

    for col in categorical_columns:
        df[col] = df[col].astype(str).fillna("Unknown")

    print("Feature engineering completed.")
    print("Columns created:")
    print(df.columns.tolist())

    return df