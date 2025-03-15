from pymongo import MongoClient
from config import Config

class Database:
    def __init__(self):
        try:
            # Sửa MONGO_URI thành MONGODB_URI để khớp với config.py
            self.client = MongoClient(Config.MONGODB_URI)
            self.db = self.client[Config.MONGODB_DB]
            print("MongoDB connected successfully")
        except Exception as e:
            print(f"MongoDB connection error: {e}")
            raise

    def get_collection(self, collection_name):
        return self.db[collection_name]

    def insert_one(self, collection_name, document):
        return self.db[collection_name].insert_one(document)

    def find(self, collection_name, query=None, projection=None):
        return self.db[collection_name].find(query or {}, projection or {})

    def close(self):
        if self.client:
            self.client.close()

db = Database()