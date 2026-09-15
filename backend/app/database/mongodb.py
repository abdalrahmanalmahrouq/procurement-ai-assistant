import os

from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv(
    "MONGODB_DB",
    "penny_procurement"
)


client = MongoClient(MONGODB_URI)

db = client[MONGODB_DB]

procurement_collection = db[os.getenv("COLLECTION_NAME", "procurement_records")]
conversations_collection = db["conversations"]
messages_collection = db["messages"]
