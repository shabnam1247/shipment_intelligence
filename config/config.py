import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

RAW_DATA_DIR = os.path.join(
    DATA_DIR,
    "raw"
)

PROCESSED_DATA_DIR = os.path.join(
    DATA_DIR,
    "processed"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "models"
)

REPORT_DIR = os.path.join(
    BASE_DIR,
    "reports"
)

MONGO_URI = os.getenv(
    "MONGO_URI"
)

MONGO_DB = os.getenv(
    "MONGO_DB",
    "shipment_intelligence"
)

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "secret_key"
)