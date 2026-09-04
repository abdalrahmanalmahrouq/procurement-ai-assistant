import os
from pathlib import Path

import numpy as np
import pandas as pd

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi


# Configuration

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "purchase_orders_cleaned.csv"
)

load_dotenv(PROJECT_ROOT / ".env")

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv(
    "MONGODB_DB",
    "penny_procurement"
)

COLLECTION_NAME = os.getenv("COLLECTION_NAME")

BATCH_SIZE = os.getenv("BATCH_SIZE")



if not MONGODB_URI:
    raise ValueError(
        "MONGODB_URI was not found in the .env file"
    )



# Connect to MongoDB Atlas

client = MongoClient(
    MONGODB_URI,
    server_api=ServerApi("1")
)

client.admin.command("ping")

print("✅ Connected to MongoDB Atlas")


db = client[DATABASE_NAME]

collection = db[COLLECTION_NAME]



# Read cleaned CSV

print("Reading cleaned dataset...")

df = pd.read_csv(
    CSV_PATH,
    parse_dates=[
        "creation_date",
        "purchase_date"
    ]
)

print(f"Rows loaded from CSV: {len(df):,}")



# Convert Pandas / NumPy values to BSON-friendly values

def to_mongo_value(value):
    """
    Convert Pandas/NumPy values into types that
    PyMongo can safely store.
    """

    # NaN / NaT → MongoDB null
    if pd.isna(value):
        return None

    # Pandas Timestamp → Python datetime
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    # NumPy number → Python int / float
    if isinstance(value, np.generic):
        return value.item()

    return value



# Import documents in batches

total_inserted = 0

for start in range(0, len(df), BATCH_SIZE):

    end = min(
        start + BATCH_SIZE,
        len(df)
    )

    batch_df = df.iloc[start:end]

    records = batch_df.to_dict(
        orient="records"
    )

    mongo_records = []

    for record in records:

        clean_record = {
            key: to_mongo_value(value)
            for key, value in record.items()
        }

        mongo_records.append(clean_record)

    result = collection.insert_many(
        mongo_records,
        ordered=False
    )

    total_inserted += len(result.inserted_ids)

    print(
        f"Inserted {total_inserted:,}"
        f" / {len(df):,}"
    )



print("\nImport completed.")

print(
    f"Inserted documents: "
    f"{total_inserted:,}"
)

print(
    f"Documents currently in MongoDB: "
    f"{collection.count_documents({}):,}"
)


client.close()