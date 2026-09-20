import os

import joblib

from sklearn.ensemble import IsolationForest


ANOMALY_FEATURES = [

    "distance_km",

    "package_weight",

    "shipping_cost",

    "delivery_days",

    "delay_days"
]


def train_anomaly_model(df):

    X = df[
        ANOMALY_FEATURES
    ]


    model = IsolationForest(

        n_estimators=200,

        contamination=0.05,

        random_state=42

    )


    model.fit(X)


    predictions = model.predict(
        X
    )


    result = df.copy()


    result["anomaly"] = (
        predictions == -1
    ).astype(int)


    os.makedirs(
        "models",
        exist_ok=True
    )


    joblib.dump(

        model,

        "models/anomaly_model.pkl"

    )


    print(
        "Anomalies detected:",
        result["anomaly"].sum()
    )


    return result