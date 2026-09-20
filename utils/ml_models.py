import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor


# =========================================================
# COMMON FEATURES
# =========================================================

FEATURES = [
    "carrier",
    "origin",
    "destination",
    "region",
    "shipping_mode",
    "priority",
    "weight",
    "distance",
    "shipping_cost",
    "promised_delivery_days",
]


# =========================================================
# PREPARE FEATURES
# =========================================================

def prepare_features(df):

    available_features = [
        col for col in FEATURES
        if col in df.columns
    ]

    if not available_features:
        raise ValueError(
            "No valid ML features found in dataset."
        )

    X = df[available_features].copy()

    # Convert numeric columns
    numeric_features = [
        "weight",
        "distance",
        "shipping_cost",
        "promised_delivery_days",
    ]

    for col in numeric_features:
        if col in X.columns:
            X[col] = pd.to_numeric(
                X[col],
                errors="coerce"
            )

    return X, available_features


# =========================================================
# CREATE PREPROCESSOR
# =========================================================

def create_preprocessor(X):

    numeric_features = X.select_dtypes(
        include=["int64", "int32", "float64", "float32"]
    ).columns.tolist()

    categorical_features = X.select_dtypes(
        include=["object", "category"]
    ).columns.tolist()

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="median")
            )
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="most_frequent")
            ),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore"
                )
            )
        ]
    )

    transformers = []

    if numeric_features:
        transformers.append(
            (
                "numeric",
                numeric_pipeline,
                numeric_features
            )
        )

    if categorical_features:
        transformers.append(
            (
                "categorical",
                categorical_pipeline,
                categorical_features
            )
        )

    preprocessor = ColumnTransformer(
        transformers=transformers
    )

    return preprocessor


# =========================================================
# DELAY CLASSIFICATION MODEL
# =========================================================

def train_delay_model(
    df,
    model_path="models/delay_model.pkl"
):

    print("\nPreparing delay model...")

    if "is_delayed" not in df.columns:
        raise ValueError(
            "Column 'is_delayed' not found."
        )

    X, features_used = prepare_features(df)

    y = pd.to_numeric(
        df["is_delayed"],
        errors="coerce"
    )

    valid_rows = y.notna()

    X = X.loc[valid_rows]
    y = y.loc[valid_rows].astype(int)

    print("Features used:")
    print(features_used)

    print("\nDelay distribution:")
    print(y.value_counts())

    preprocessor = create_preprocessor(X)

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced"
    )

    pipeline = Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor
            ),
            (
                "model",
                model
            )
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    pipeline.fit(X_train, y_train)

    accuracy = pipeline.score(
        X_test,
        y_test
    )

    print(
        f"\nDelay model accuracy: {accuracy:.2f}"
    )

    os.makedirs(
        os.path.dirname(model_path),
        exist_ok=True
    )

    joblib.dump(
        pipeline,
        model_path
    )

    print(
        f"Delay model saved to: {model_path}"
    )

    return pipeline


# =========================================================
# DELIVERY TIME REGRESSION MODEL
# =========================================================

def train_delivery_model(
    df,
    model_path="models/delivery_model.pkl"
):

    print("\nPreparing delivery-time model...")

    if "actual_delivery_days" not in df.columns:
        raise ValueError(
            "Column 'actual_delivery_days' not found."
        )

    X, features_used = prepare_features(df)

    y = pd.to_numeric(
        df["actual_delivery_days"],
        errors="coerce"
    )

    valid_rows = y.notna()

    X = X.loc[valid_rows]
    y = y.loc[valid_rows]

    print("Features used:")
    print(features_used)

    preprocessor = create_preprocessor(X)

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42
    )

    pipeline = Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor
            ),
            (
                "model",
                model
            )
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    pipeline.fit(
        X_train,
        y_train
    )

    score = pipeline.score(
        X_test,
        y_test
    )

    print(
        f"\nDelivery model R² score: {score:.2f}"
    )

    os.makedirs(
        os.path.dirname(model_path),
        exist_ok=True
    )

    joblib.dump(
        pipeline,
        model_path
    )

    print(
        f"Delivery model saved to: {model_path}"
    )

    return pipeline