# Model definition for tour
# Created: 2025-03-04 23:44:55
# Author: thuanpony03

from datetime import datetime
from bson import ObjectId

class Tour:
    def __init__(self, name, description, destination, duration, price, inclusions=None, exclusions=None, departure_dates=None, images=None, min_people=1):
        self.name = name
        self.description = description
        self.destination = destination  # ObjectId hoặc mảng ObjectId tham chiếu đến Location
        self.duration = duration  # Ví dụ: "5 ngày 4 đêm"
        self.price = price  # Giá cơ bản
        self.inclusions = inclusions or []  # Những gì bao gồm trong tour
        self.exclusions = exclusions or []  # Những gì không bao gồm
        self.departure_dates = departure_dates or []  # Các ngày khởi hành
        self.images = images or []  # Link ảnh về tour
        self.min_people = min_people  # Số người tối thiểu
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "destination": self.destination,
            "duration": self.duration,
            "price": self.price,
            "inclusions": self.inclusions,
            "exclusions": self.exclusions,
            "departure_dates": self.departure_dates,
            "images": self.images,
            "min_people": self.min_people,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @staticmethod
    def from_dict(data):
        tour = Tour(
            data["name"],
            data["description"],
            data["destination"],
            data["duration"],
            data["price"],
            data.get("inclusions"),
            data.get("exclusions"),
            data.get("departure_dates"),
            data.get("images"),
            data.get("min_people", 1)
        )
        if "created_at" in data:
            tour.created_at = data["created_at"]
        if "updated_at" in data:
            tour.updated_at = data["updated_at"]
        return tour