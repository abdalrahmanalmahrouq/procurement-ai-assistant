import os

from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))

db = client[os.getenv("MONGODB_DB", "procurement_ai_assistant")]
collection = db[os.getenv("COLLECTION_NAME", "procurement_records")]
conversations = db["conversations"]
messages = db["messages"]


collection.create_index("order_key")

collection.create_index("creation_date")

collection.create_index([
    ("year", 1),
    ("quarter", 1)
])

collection.create_index("supplier_name")

collection.create_index("department_name")

collection.create_index("item_name")

conversations.create_index("updated_at")
messages.create_index([("conversation_id", 1), ("created_at", 1)])
messages.create_index(
    [("conversation_id", 1), ("turn_id", 1), ("role", 1)],
    unique=True,
)


print("MongoDB indexes created successfully.")

client.close()
