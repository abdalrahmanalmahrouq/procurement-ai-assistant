import os

from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))

db = client[os.getenv("MONGODB_DB")]
collection = db[os.getenv("COLLECTION_NAME")]


collection.create_index("order_key")

collection.create_index("creation_date")

collection.create_index([
    ("year", 1),
    ("quarter", 1)
])

collection.create_index("supplier_name")

collection.create_index("department_name")

collection.create_index("item_name")


print("MongoDB indexes created successfully.")

client.close()