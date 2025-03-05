# Service for database
# Created: 2025-03-04 23:44:55
# Author: thuanpony03

from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Nạp biến môi trường
load_dotenv()

class Database:
    def __init__(self):
        self.client = MongoClient(os.getenv('MONGODB_URI'))
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
        
    def get_collection(self, collection_name):
        return self.db[collection_name]
        
    def close(self):
        self.client.close()

# Khởi tạo đối tượng Database để sử dụng trong toàn ứng dụng
db = Database()