import os

from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client[os.getenv("MONGODB_DB", "procurement_ai_assistant")]

procurement_collection = db[os.getenv("COLLECTION_NAME", "procurement_records")]
conversations_collection = db["conversations"]
messages_collection = db["messages"]
