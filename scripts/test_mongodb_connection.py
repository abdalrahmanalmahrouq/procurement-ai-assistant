import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi


load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

client = MongoClient(
    MONGODB_URI,
    server_api=ServerApi("1")
)

try:
    client.admin.command("ping")
    print("✅ Successfully connected to MongoDB Atlas!")

except Exception as e:
    print("❌ MongoDB connection failed:")
    print(e)

finally:
    client.close()