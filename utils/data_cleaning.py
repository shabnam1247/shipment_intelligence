import pandas as pd


DATE_COLUMNS = [
    "order_date",
    "ship_date",
    "expected_delivery_date",
    "actual_delivery_date"
]


NUMERIC_COLUMNS = [
    "distance_km",
    "package_weight",
    "shipping_cost",
    "warehouse_delay",
    "customs_delay"
]


CATEGORICAL_COLUMNS = [
    "carrier",
    "origin",
    "destination",
    "region",
    "shipping_mode",
    "weather",
    "traffic_level",
    "vehicle_type",
    "order_priority"
]


def clean_shipment_data(df):

    df = df.copy()


    # Convert dates

    for column in DATE_COLUMNS:

        if column in df.columns:

            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            )


    # Convert numbers

    for column in NUMERIC_COLUMNS:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )


    # Remove duplicates

    if "shipment_id" in df.columns:

        df = df.drop_duplicates(
            subset=["shipment_id"]
        )


    # Numeric missing values

    for column in NUMERIC_COLUMNS:

        if column in df.columns:

            df[column] = df[column].fillna(
                df[column].median()
            )


    # Categorical missing values

    for column in CATEGORICAL_COLUMNS:

        if column in df.columns:

            df[column] = df[column].fillna(
                "Unknown"
            )


    return df