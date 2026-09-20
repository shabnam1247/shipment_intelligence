import os
import io
import joblib
import pandas as pd

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    send_file,
    flash
)

from werkzeug.utils import secure_filename

from utils.mongodb import (
    get_shipments_collection,
    test_connection
)


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

app.secret_key = "shipment-intelligence-secret-key"

UPLOAD_FOLDER = "data/raw"

ALLOWED_EXTENSIONS = {
    "csv",
    "xlsx",
    "xls"
}

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ============================================================
# MODEL PATHS
# ============================================================

DELAY_MODEL_PATH = os.path.join(
    "models",
    "delay_model.pkl"
)

DELIVERY_MODEL_PATH = os.path.join(
    "models",
    "delivery_model.pkl"
)

ANOMALY_MODEL_PATH = os.path.join(
    "models",
    "anomaly_model.pkl"
)


# ============================================================
# GLOBAL MODELS
# ============================================================

delay_model = None
delivery_model = None
anomaly_model = None


# ============================================================
# LOAD MODELS
# ============================================================

def load_models():

    global delay_model
    global delivery_model
    global anomaly_model

    print("\nLoading ML models...")

    # Delay model
    if os.path.exists(DELAY_MODEL_PATH):

        try:
            delay_model = joblib.load(
                DELAY_MODEL_PATH
            )

            print(
                "Delay model loaded."
            )

        except Exception as e:

            print(
                "Error loading delay model:",
                e
            )

    else:

        print(
            "WARNING: delay_model.pkl not found."
        )

    # Delivery model
    if os.path.exists(DELIVERY_MODEL_PATH):

        try:

            delivery_model = joblib.load(
                DELIVERY_MODEL_PATH
            )

            print(
                "Delivery model loaded."
            )

        except Exception as e:

            print(
                "Error loading delivery model:",
                e
            )

    else:

        print(
            "WARNING: delivery_model.pkl not found."
        )

    # Anomaly model
    if os.path.exists(ANOMALY_MODEL_PATH):

        try:

            anomaly_model = joblib.load(
                ANOMALY_MODEL_PATH
            )

            print(
                "Anomaly model loaded."
            )

        except Exception as e:

            print(
                "Error loading anomaly model:",
                e
            )

    else:

        print(
            "WARNING: anomaly_model.pkl not found."
        )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_float(value, default=0):

    try:

        if value is None:
            return default

        if pd.isna(value):
            return default

        return float(value)

    except (
        ValueError,
        TypeError
    ):

        return default


def safe_round(value, digits=2):

    try:

        if value is None:
            return 0

        if pd.isna(value):
            return 0

        return round(
            float(value),
            digits
        )

    except (
        ValueError,
        TypeError
    ):

        return 0


def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(
            ".",
            1
        )[1].lower()
        in ALLOWED_EXTENSIONS
    )


def get_dataframe():

    try:

        collection = get_shipments_collection()

        records = list(
            collection.find(
                {},
                {
                    "_id": 0
                }
            )
        )

        if not records:

            return pd.DataFrame()

        return pd.DataFrame(
            records
        )

    except Exception as e:

        print(
            "MongoDB data error:",
            e
        )

        return pd.DataFrame()


def clean_dataframe(df):

    if df.empty:

        return df

    # Remove MongoDB internal id if present
    if "_id" in df.columns:

        df = df.drop(
            columns=["_id"]
        )

    # Numeric columns
    numeric_columns = [
        "weight",
        "distance",
        "shipping_cost",
        "promised_delivery_days",
        "actual_delivery_days",
        "is_delayed",
        "delivery_delay_days"
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


# ============================================================
# DELAY MODEL PREDICTION
# ============================================================

def create_model_input(df):

    """
    Features used while training the delay/delivery models.
    These match the features printed by train_models.py.
    """

    features = [
        "carrier",
        "origin",
        "destination",
        "region",
        "shipping_mode",
        "priority",
        "weight",
        "distance",
        "shipping_cost",
        "promised_delivery_days"
    ]

    X = df.copy()

    # Make sure every expected feature exists
    for column in features:

        if column not in X.columns:

            if column in [
                "weight",
                "distance",
                "shipping_cost",
                "promised_delivery_days"
            ]:

                X[column] = 0

            else:

                X[column] = "Unknown"

    X = X[features].copy()

    return X


def predict_delay(df):

    if delay_model is None:

        return (
            [0] * len(df),
            [0] * len(df)
        )

    try:

        X = create_model_input(
            df
        )

        predictions = delay_model.predict(
            X
        )

        if hasattr(
            delay_model,
            "predict_proba"
        ):

            probabilities = (
                delay_model
                .predict_proba(X)[:, 1]
                * 100
            )

        else:

            probabilities = (
                predictions * 100
            )

        return (
            predictions,
            probabilities
        )

    except Exception as e:

        print(
            "Delay prediction error:",
            e
        )

        return (
            [0] * len(df),
            [0] * len(df)
        )


# ============================================================
# DELIVERY TIME PREDICTION
# ============================================================

def predict_delivery(df):

    if delivery_model is None:

        return [
            0
            for _ in range(len(df))
        ]

    try:

        X = create_model_input(
            df
        )

        predictions = delivery_model.predict(
            X
        )

        return [
            safe_round(x)
            for x in predictions
        ]

    except Exception as e:

        print(
            "Delivery prediction error:",
            e
        )

        return [
            0
            for _ in range(len(df))
        ]


# ============================================================
# ANOMALY DETECTION
# ============================================================

def calculate_anomalies(df):

    if (
        anomaly_model is None
        or df.empty
    ):

        return 0

    try:

        working = df.copy()

        # Create delay days if not already present
        if (
            "delivery_delay_days"
            not in working.columns
        ):

            if (
                "actual_delivery_days"
                in working.columns
                and
                "promised_delivery_days"
                in working.columns
            ):

                working[
                    "delivery_delay_days"
                ] = (
                    pd.to_numeric(
                        working[
                            "actual_delivery_days"
                        ],
                        errors="coerce"
                    )
                    -
                    pd.to_numeric(
                        working[
                            "promised_delivery_days"
                        ],
                        errors="coerce"
                    )
                )

        # Possible numeric anomaly features
        features = [
            "weight",
            "distance",
            "shipping_cost",
            "promised_delivery_days",
            "actual_delivery_days",
            "delivery_delay_days"
        ]

        available = [
            column
            for column in features
            if column in working.columns
        ]

        if not available:

            return 0

        X = working[
            available
        ].copy()

        for column in available:

            X[column] = pd.to_numeric(
                X[column],
                errors="coerce"
            )

        # Fill missing values
        X = X.fillna(
            X.median(
                numeric_only=True
            )
        )

        X = X.fillna(0)

        model = anomaly_model

        # Support saved dictionary format
        if isinstance(
            anomaly_model,
            dict
        ):

            model = anomaly_model.get(
                "model"
            )

            model_features = (
                anomaly_model.get(
                    "features"
                )
            )

            if (
                model_features
                and
                all(
                    col in X.columns
                    for col in model_features
                )
            ):

                X = X[
                    model_features
                ]

        if model is None:

            return 0

        predictions = model.predict(
            X
        )

        return int(
            (predictions == -1).sum()
        )

    except Exception as e:

        print(
            "Anomaly detection error:",
            e
        )

        return 0


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def dashboard():

    print(
        "\nLoading dashboard..."
    )

    df = get_dataframe()

    df = clean_dataframe(
        df
    )

    # --------------------------------------------------------
    # Empty database
    # --------------------------------------------------------

    if df.empty:

        return render_template(
            "dashboard.html",

            total_shipments=0,

            delayed_shipments=0,

            delay_rate=0,

            avg_delivery=0,

            anomaly_count=0,

            monthly_labels=[],

            monthly_values=[],

            carrier_labels=[],

            carrier_values=[],

            region_labels=[],

            region_values=[],

            mode_labels=[],

            mode_values=[],

            high_risk_shipments=[]
        )

    # --------------------------------------------------------
    # TOTAL SHIPMENTS
    # --------------------------------------------------------

    total_shipments = len(
        df
    )

    # --------------------------------------------------------
    # DELAYED SHIPMENTS
    # --------------------------------------------------------

    if "is_delayed" in df.columns:

        delayed_column = pd.to_numeric(
            df["is_delayed"],
            errors="coerce"
        ).fillna(0)

        delayed_shipments = int(
            (
                delayed_column == 1
            ).sum()
        )

    else:

        delayed_shipments = 0

    # --------------------------------------------------------
    # DELAY RATE
    # --------------------------------------------------------

    if total_shipments > 0:

        delay_rate = (
            delayed_shipments
            /
            total_shipments
        ) * 100

    else:

        delay_rate = 0

    delay_rate = safe_round(
        delay_rate
    )

    # --------------------------------------------------------
    # AVERAGE DELIVERY
    # --------------------------------------------------------

    avg_delivery = 0

    if (
        "actual_delivery_days"
        in df.columns
    ):

        delivery_values = pd.to_numeric(
            df[
                "actual_delivery_days"
            ],
            errors="coerce"
        ).dropna()

        if not delivery_values.empty:

            avg_delivery = safe_round(
                delivery_values.mean()
            )

    # --------------------------------------------------------
    # ANOMALIES
    # --------------------------------------------------------

    anomaly_count = calculate_anomalies(
        df
    )

    # ========================================================
    # MONTHLY SHIPMENT TREND
    # ========================================================

    monthly_labels = []

    monthly_values = []

    if "shipment_date" in df.columns:

        # IMPORTANT:
        # Convert the actual dataframe column to datetime
        df["shipment_date"] = pd.to_datetime(
            df["shipment_date"],
            errors="coerce"
        )

        # Remove invalid dates
        monthly_df = df.dropna(
            subset=[
                "shipment_date"
            ]
        ).copy()

        if not monthly_df.empty:

            # Create month column
            monthly_df["month"] = (
                monthly_df[
                    "shipment_date"
                ]
                .dt.to_period("M")
                .astype(str)
            )

            # Count shipments by month
            monthly_data = (
                monthly_df
                .groupby("month")
                .size()
                .sort_index()
            )

            monthly_labels = [
                str(x)
                for x in monthly_data.index
            ]

            monthly_values = [
                int(x)
                for x in monthly_data.values
            ]

    # ========================================================
    # DELAY BY CARRIER
    # ========================================================

    carrier_labels = []

    carrier_values = []

    if (
        "carrier" in df.columns
        and
        "is_delayed" in df.columns
    ):

        carrier_df = df.copy()

        carrier_df[
            "is_delayed"
        ] = pd.to_numeric(
            carrier_df[
                "is_delayed"
            ],
            errors="coerce"
        ).fillna(0)

        carrier_data = (
            carrier_df
            .groupby("carrier")[
                "is_delayed"
            ]
            .mean()
            .mul(100)
            .round(2)
        )

        carrier_labels = [
            str(x)
            for x in carrier_data.index
        ]

        carrier_values = [
            float(x)
            for x in carrier_data.values
        ]

    # ========================================================
    # DELAY BY REGION
    # ========================================================

    region_labels = []

    region_values = []

    if (
        "region" in df.columns
        and
        "is_delayed" in df.columns
    ):

        region_df = df.copy()

        region_df[
            "is_delayed"
        ] = pd.to_numeric(
            region_df[
                "is_delayed"
            ],
            errors="coerce"
        ).fillna(0)

        region_data = (
            region_df
            .groupby("region")[
                "is_delayed"
            ]
            .mean()
            .mul(100)
            .round(2)
        )

        region_labels = [
            str(x)
            for x in region_data.index
        ]

        region_values = [
            float(x)
            for x in region_data.values
        ]

    # ========================================================
    # DELAY BY SHIPPING MODE
    # ========================================================

    mode_labels = []

    mode_values = []

    if (
        "shipping_mode" in df.columns
        and
        "is_delayed" in df.columns
    ):

        mode_df = df.copy()

        mode_df[
            "is_delayed"
        ] = pd.to_numeric(
            mode_df[
                "is_delayed"
            ],
            errors="coerce"
        ).fillna(0)

        mode_data = (
            mode_df
            .groupby(
                "shipping_mode"
            )[
                "is_delayed"
            ]
            .mean()
            .mul(100)
            .round(2)
        )

        mode_labels = [
            str(x)
            for x in mode_data.index
        ]

        mode_values = [
            float(x)
            for x in mode_data.values
        ]

    # ========================================================
    # HIGH RISK SHIPMENTS
    # ========================================================

    high_risk_shipments = []

    if (
        delay_model is not None
        and not df.empty
    ):

        try:

            predictions, probabilities = (
                predict_delay(df)
            )

            temp = df.copy()

            temp[
                "prediction"
            ] = predictions

            temp[
                "risk_probability"
            ] = probabilities

            temp = temp.sort_values(
                "risk_probability",
                ascending=False
            )

            for _, row in temp.head(
                10
            ).iterrows():

                prediction = row.get(
                    "prediction",
                    0
                )

                high_risk_shipments.append(
                    {
                        "shipment_id":
                            str(
                                row.get(
                                    "shipment_id",
                                    ""
                                )
                            ),

                        "carrier":
                            str(
                                row.get(
                                    "carrier",
                                    ""
                                )
                            ),

                        "region":
                            str(
                                row.get(
                                    "region",
                                    ""
                                )
                            ),

                        "risk":
                            safe_round(
                                row.get(
                                    "risk_probability",
                                    0
                                )
                            ),

                        "prediction":
                            (
                                "Delayed"
                                if prediction == 1
                                else "On Time"
                            )
                    }
                )

        except Exception as e:

            print(
                "High-risk calculation error:",
                e
            )

    # ========================================================
    # SEND DATA TO TEMPLATE
    # ========================================================

    return render_template(
        "dashboard.html",

        total_shipments=
            total_shipments,

        delayed_shipments=
            delayed_shipments,

        delay_rate=
            delay_rate,

        avg_delivery=
            avg_delivery,

        anomaly_count=
            anomaly_count,

        monthly_labels=
            monthly_labels,

        monthly_values=
            monthly_values,

        carrier_labels=
            carrier_labels,

        carrier_values=
            carrier_values,

        region_labels=
            region_labels,

        region_values=
            region_values,

        mode_labels=
            mode_labels,

        mode_values=
            mode_values,

        high_risk_shipments=
            high_risk_shipments
    )


# ============================================================
# SHIPMENTS PAGE
# ============================================================

@app.route("/shipments")
def shipments():

    df = get_dataframe()

    df = clean_dataframe(
        df
    )

    if df.empty:

        shipments_data = []

    else:

        # Convert NaN to empty strings
        df = df.fillna("")

        shipments_data = (
            df.to_dict(
                orient="records"
            )
        )

    return render_template(
        "shipments.html",
        shipments=shipments_data
    )


# ============================================================
# SHIPMENT DETAILS
# ============================================================

@app.route(
    "/shipment/<shipment_id>"
)
def shipment_detail(
    shipment_id
):

    collection = get_shipments_collection()

    shipment = collection.find_one(
        {
            "shipment_id":
                shipment_id
        },
        {
            "_id": 0
        }
    )

    if shipment is None:

        return (
            "Shipment not found",
            404
        )

    return render_template(
        "shipment_detail.html",
        shipment=shipment
    )


# ============================================================
# PREDICTIONS PAGE
# ============================================================

@app.route("/predictions")
def predictions():

    df = get_dataframe()

    df = clean_dataframe(
        df
    )

    predictions_data = []

    if (
        not df.empty
        and delay_model is not None
    ):

        try:

            delay_predictions, risk_values = (
                predict_delay(df)
            )

            delivery_predictions = (
                predict_delivery(df)
            )

            for i, (_, row) in enumerate(
                df.iterrows()
            ):

                predictions_data.append(
                    {
                        "shipment_id":
                            str(
                                row.get(
                                    "shipment_id",
                                    ""
                                )
                            ),

                        "carrier":
                            str(
                                row.get(
                                    "carrier",
                                    ""
                                )
                            ),

                        "region":
                            str(
                                row.get(
                                    "region",
                                    ""
                                )
                            ),

                        "shipping_mode":
                            str(
                                row.get(
                                    "shipping_mode",
                                    ""
                                )
                            ),

                        "delay_prediction":
                            (
                                "Delayed"
                                if delay_predictions[i]
                                == 1
                                else "On Time"
                            ),

                        "risk":
                            safe_round(
                                risk_values[i]
                            ),

                        "predicted_delivery_days":
                            safe_round(
                                delivery_predictions[i]
                            )
                    }
                )

        except Exception as e:

            print(
                "Prediction page error:",
                e
            )

    return render_template(
        "predictions.html",
        predictions=predictions_data
    )


# ============================================================
# ANOMALIES PAGE
# ============================================================

@app.route("/anomalies")
def anomalies():

    df = get_dataframe()

    df = clean_dataframe(
        df
    )

    anomalies_data = []

    if (
        not df.empty
        and anomaly_model is not None
    ):

        try:

            working = df.copy()

            # Create delivery delay
            if (
                "delivery_delay_days"
                not in working.columns
            ):

                if (
                    "actual_delivery_days"
                    in working.columns
                    and
                    "promised_delivery_days"
                    in working.columns
                ):

                    working[
                        "delivery_delay_days"
                    ] = (
                        pd.to_numeric(
                            working[
                                "actual_delivery_days"
                            ],
                            errors="coerce"
                        )
                        -
                        pd.to_numeric(
                            working[
                                "promised_delivery_days"
                            ],
                            errors="coerce"
                        )
                    )

            anomaly_features = [
                "weight",
                "distance",
                "shipping_cost",
                "promised_delivery_days",
                "actual_delivery_days",
                "delivery_delay_days"
            ]

            available = [
                column
                for column in anomaly_features
                if column in working.columns
            ]

            if available:

                X = working[
                    available
                ].copy()

                for column in available:

                    X[column] = pd.to_numeric(
                        X[column],
                        errors="coerce"
                    )

                X = X.fillna(
                    X.median(
                        numeric_only=True
                    )
                )

                X = X.fillna(0)

                model = anomaly_model

                if isinstance(
                    anomaly_model,
                    dict
                ):

                    model = anomaly_model.get(
                        "model"
                    )

                    model_features = (
                        anomaly_model.get(
                            "features"
                        )
                    )

                    if (
                        model_features
                        and
                        all(
                            col in X.columns
                            for col in model_features
                        )
                    ):

                        X = X[
                            model_features
                        ]

                if model is not None:

                    results = model.predict(
                        X
                    )

                    for i, result in enumerate(
                        results
                    ):

                        if result == -1:

                            row = working.iloc[
                                i
                            ]

                            anomalies_data.append(
                                {
                                    "shipment_id":
                                        str(
                                            row.get(
                                                "shipment_id",
                                                ""
                                            )
                                        ),

                                    "carrier":
                                        str(
                                            row.get(
                                                "carrier",
                                                ""
                                            )
                                        ),

                                    "region":
                                        str(
                                            row.get(
                                                "region",
                                                ""
                                            )
                                        ),

                                    "weight":
                                        safe_round(
                                            row.get(
                                                "weight",
                                                0
                                            )
                                        ),

                                    "distance":
                                        safe_round(
                                            row.get(
                                                "distance",
                                                0
                                            )
                                        ),

                                    "shipping_cost":
                                        safe_round(
                                            row.get(
                                                "shipping_cost",
                                                0
                                            )
                                        ),

                                    "delay_days":
                                        safe_round(
                                            row.get(
                                                "delivery_delay_days",
                                                0
                                            )
                                        )
                                }
                            )

        except Exception as e:

            print(
                "Anomaly page error:",
                e
            )

    return render_template(
        "anomalies.html",
        anomalies=anomalies_data
    )


# ============================================================
# UPLOAD PAGE
# ============================================================

@app.route("/upload")
def upload():

    return render_template(
        "upload.html"
    )


# ============================================================
# UPLOAD FILE
# ============================================================

@app.route(
    "/upload",
    methods=["POST"]
)
def upload_file():

    if "file" not in request.files:

        flash(
            "Please select a file."
        )

        return redirect(
            url_for("upload")
        )

    file = request.files["file"]

    if file.filename == "":

        flash(
            "No file selected."
        )

        return redirect(
            url_for("upload")
        )

    if not allowed_file(
        file.filename
    ):

        flash(
            "Only CSV, XLSX and XLS files are allowed."
        )

        return redirect(
            url_for("upload")
        )

    try:

        filename = secure_filename(
            file.filename
        )

        extension = (
            filename
            .rsplit(
                ".",
                1
            )[1]
            .lower()
        )

        # ----------------------------------------------------
        # Read file
        # ----------------------------------------------------

        if extension == "csv":

            df = pd.read_csv(
                file
            )

        else:

            df = pd.read_excel(
                file
            )

        # ----------------------------------------------------
        # Normalize columns
        # ----------------------------------------------------

        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(
                " ",
                "_",
                regex=False
            )
        )

        # ----------------------------------------------------
        # Convert NaN to None
        # ----------------------------------------------------

        df = df.where(
            pd.notnull(df),
            None
        )

        records = df.to_dict(
            orient="records"
        )

        # ----------------------------------------------------
        # MongoDB
        # ----------------------------------------------------

        collection = (
            get_shipments_collection()
        )

        # Replace old dataset
        collection.delete_many({})

        if records:

            collection.insert_many(
                records
            )

        # ----------------------------------------------------
        # Save file
        # ----------------------------------------------------

        file_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        if extension == "csv":

            df.to_csv(
                file_path,
                index=False
            )

        else:

            df.to_excel(
                file_path,
                index=False
            )

        flash(
            f"Successfully uploaded {len(records)} shipments."
        )

        return redirect(
            url_for("dashboard")
        )

    except Exception as e:

        print(
            "Upload error:",
            e
        )

        flash(
            f"Upload failed: {e}"
        )

        return redirect(
            url_for("upload")
        )


# ============================================================
# DOWNLOAD REPORT
# ============================================================

@app.route(
    "/download-report"
)
def download_report():

    df = get_dataframe()

    if df.empty:

        df = pd.DataFrame(
            columns=[
                "shipment_id",
                "carrier",
                "region",
                "shipping_mode",
                "is_delayed"
            ]
        )

    output = io.StringIO()

    df.to_csv(
        output,
        index=False
    )

    output.seek(0)

    return send_file(
        io.BytesIO(
            output.getvalue().encode(
                "utf-8"
            )
        ),
        mimetype="text/csv",
        as_attachment=True,
        download_name="shipment_report.csv"
    )


# ============================================================
# API - ALL SHIPMENTS
# ============================================================

@app.route(
    "/api/shipments"
)
def api_shipments():

    df = get_dataframe()

    df = clean_dataframe(
        df
    )

    if df.empty:

        return jsonify([])

    df = df.fillna("")

    return jsonify(
        df.to_dict(
            orient="records"
        )
    )


# ============================================================
# API - KPIs
# ============================================================

@app.route(
    "/api/kpis"
)
def api_kpis():

    df = get_dataframe()

    df = clean_dataframe(
        df
    )

    if df.empty:

        return jsonify(
            {
                "total_shipments": 0,
                "delayed_shipments": 0,
                "delay_rate": 0,
                "avg_delivery": 0,
                "anomalies": 0
            }
        )

    total_shipments = len(
        df
    )

    # Delayed
    if "is_delayed" in df.columns:

        delayed = (
            pd.to_numeric(
                df[
                    "is_delayed"
                ],
                errors="coerce"
            )
            .fillna(0)
        )

        delayed_shipments = int(
            (
                delayed == 1
            ).sum()
        )

    else:

        delayed_shipments = 0

    # Delay rate
    if total_shipments > 0:

        delay_rate = (
            delayed_shipments
            /
            total_shipments
        ) * 100

    else:

        delay_rate = 0

    # Average delivery
    avg_delivery = 0

    if (
        "actual_delivery_days"
        in df.columns
    ):

        values = pd.to_numeric(
            df[
                "actual_delivery_days"
            ],
            errors="coerce"
        ).dropna()

        if not values.empty:

            avg_delivery = values.mean()

    # Anomalies
    anomaly_count = calculate_anomalies(
        df
    )

    return jsonify(
        {
            "total_shipments":
                total_shipments,

            "delayed_shipments":
                delayed_shipments,

            "delay_rate":
                safe_round(
                    delay_rate
                ),

            "avg_delivery":
                safe_round(
                    avg_delivery
                ),

            "anomalies":
                anomaly_count
        }
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/health"
)
def health():

    try:

        collection = (
            get_shipments_collection()
        )

        count = collection.count_documents(
            {}
        )

        return jsonify(
            {
                "status": "online",
                "mongodb": "connected",
                "shipments": count,
                "delay_model":
                    delay_model is not None,
                "delivery_model":
                    delivery_model is not None,
                "anomaly_model":
                    anomaly_model is not None
            }
        )

    except Exception as e:

        return jsonify(
            {
                "status": "error",
                "message": str(e)
            }
        ), 500


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):

    return (
        "Page not found",
        404
    )


@app.errorhandler(500)
def server_error(error):

    return (
        "Internal Server Error",
        500
    )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    print(
        "\nStarting Shipment Intelligence..."
    )

    # MongoDB
    try:

        test_connection()

    except Exception as e:

        print(
            "MongoDB connection error:",
            e
        )

    # ML models
    load_models()

    print(
        "\nShipment Intelligence is ready!"
    )

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )