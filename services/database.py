from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Database:
    def __init__(self):
        # Connect to local MongoDB
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client.travel_chatbot
        
        # Collections
        self.locations = self.db.locations
        self.tours = self.db.tours
        self.hotels = self.db.hotels
        self.visas = self.db.visas
        self.flights = self.db.flights
        self.passports = self.db.passports
        self.bookings = self.db.bookings
        self.conversations = self.db.conversations
        self.faqs = self.db.faqs
        self.users = self.db.users
        
    def get_collection(self, collection_name):
        return self.db[collection_name]
        
    def close(self):
        self.client.close()

# Create instance
db = Database()