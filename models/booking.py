# Model definition for booking
# Created: 2025-03-06 23:44:55
# Author: thuanpony03

from datetime import datetime
from bson import ObjectId

class Booking:
    def __init__(self, user_id, service_type, service_id, user_name=None, user_phone=None,
                 travel_date=None, num_adults=1, num_children=0, total_price=0, 
                 status="pending", payment_method=None, notes=None):
        self.user_id = user_id
        self.service_type = service_type  # "tour", "visa", "flight"
        self.service_id = service_id  # ObjectId tham chiếu đến dịch vụ
        self.user_name = user_name
        self.user_phone = user_phone
        self.travel_date = travel_date  # Ngày khởi hành
        self.num_adults = num_adults
        self.num_children = num_children
        self.total_price = total_price
        self.status = status  # "pending", "confirmed", "cancelled", "completed"
        self.payment_method = payment_method  # "cash", "transfer", "card"
        self.notes = notes
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "service_type": self.service_type,
            "service_id": self.service_id,
            "user_name": self.user_name,
            "user_phone": self.user_phone,
            "travel_date": self.travel_date,
            "num_adults": self.num_adults,
            "num_children": self.num_children,
            "total_price": self.total_price,
            "status": self.status,
            "payment_method": self.payment_method,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @staticmethod
    def from_dict(data):
        booking = Booking(
            data["user_id"],
            data["service_type"],
            data["service_id"],
            data.get("user_name"),
            data.get("user_phone"),
            data.get("travel_date"),
            data.get("num_adults", 1),
            data.get("num_children", 0),
            data.get("total_price", 0),
            data.get("status", "pending"),
            data.get("payment_method"),
            data.get("notes")
        )
        if "created_at" in data:
            booking.created_at = data["created_at"]
        if "updated_at" in data:
            booking.updated_at = data["updated_at"]
        return booking