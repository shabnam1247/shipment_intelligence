from utils.mongodb import insert_many_shipments
import pandas as pd


CSV_PATH = "data/raw/shipments.csv"


print("Loading shipment CSV...")

df = pd.read_csv(CSV_PATH)

print(f"Rows found: {len(df)}")


# Convert NaN to None
df = df.where(
    pd.notnull(df),
    None
)

records = df.to_dict(
    orient="records"
)


print("Uploading to MongoDB...")

count = insert_many_shipments(records)

print(f"{count} shipments inserted into MongoDB.")