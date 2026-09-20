from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

# MongoDB settings
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017/"
)

MONGO_DB = os.getenv(
    "MONGO_DB",
    "shipment_intelligence"
)

MONGO_COLLECTION = os.getenv(
    "MONGO_COLLECTION",
    "shipments"
)


# MongoDB connection
client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client[MONGO_DB]

shipments_collection = db[MONGO_COLLECTION]


# ------------------------------------------------
# GET SHIPMENTS COLLECTION
# ------------------------------------------------

def get_shipments_collection():
    return shipments_collection


# ------------------------------------------------
# TEST CONNECTION
# ------------------------------------------------

def test_connection():

    try:
        client.admin.command("ping")

        print("MongoDB Connected Successfully!")
        print("Database:", MONGO_DB)
        print("Collection:", MONGO_COLLECTION)

        return True

    except Exception as e:

        print("MongoDB Connection Failed!")
        print(e)

        return False


# ------------------------------------------------
# GET ALL SHIPMENTS
# ------------------------------------------------

def get_all_shipments():

    return list(
        shipments_collection.find(
            {},
            {"_id": 0}
        )
    )


# ------------------------------------------------
# GET SINGLE SHIPMENT
# ------------------------------------------------

def get_shipment_by_id(shipment_id):

    return shipments_collection.find_one(
        {
            "shipment_id": shipment_id
        },
        {
            "_id": 0
        }
    )


# ------------------------------------------------
# INSERT ONE SHIPMENT
# ------------------------------------------------

def insert_shipment(shipment):

    result = shipments_collection.insert_one(
        shipment
    )

    return result.inserted_id


# ------------------------------------------------
# INSERT MANY SHIPMENTS
# ------------------------------------------------

def insert_many_shipments(shipments):

    if not shipments:
        return 0

    result = shipments_collection.insert_many(
        shipments
    )

    return len(result.inserted_ids)


# ------------------------------------------------
# DELETE ALL
# ------------------------------------------------

def delete_all_shipments():

    result = shipments_collection.delete_many({})

    return result.deleted_count