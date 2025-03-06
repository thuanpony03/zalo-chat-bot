# Service for tour_service
# Created: 2025-03-04 23:44:55
# Author: thuanpony03

from services.database import db
from bson import ObjectId
import re
from datetime import datetime

class TourService:
    def __init__(self):
        pass
        
    def search_tours(self, **kwargs):
        """Tìm kiếm tour dựa trên các tiêu chí"""
        query = {}
        
        # Tìm theo điểm đến
        if "destination" in kwargs:
            destination = kwargs["destination"]
            # Tìm ID của điểm đến từ tên
            location = db.locations.find_one(
                {"$or": [
                    {"name": {"$regex": f".*{destination}.*", "$options": "i"}},
                    {"popular_cities": {"$in": [re.compile(f".*{destination}.*", re.IGNORECASE)]}}
                ]}
            )
            
            if location:
                query["destination"] = location["_id"]
            else:
                # Nếu không tìm thấy location, tìm theo tên tour
                query["name"] = {"$regex": f".*{destination}.*", "$options": "i"}
                
        # Tìm theo khoảng giá
        if "price_min" in kwargs and "price_max" in kwargs:
            query["price"] = {
                "$gte": kwargs["price_min"],
                "$lte": kwargs["price_max"]
            }
        elif "price_min" in kwargs:
            query["price"] = {"$gte": kwargs["price_min"]}
        elif "price_max" in kwargs:
            query["price"] = {"$lte": kwargs["price_max"]}
            
        # Tìm theo thời gian
        if "duration" in kwargs:
            query["duration"] = {"$regex": kwargs["duration"], "$options": "i"}
            
        # Thực hiện truy vấn
        tours = list(db.tours.find(query))
        
        # Thêm thông tin tên điểm đến
        for tour in tours:
            if "destination" in tour and isinstance(tour["destination"], ObjectId):
                location = db.locations.find_one({"_id": tour["destination"]})
                if location:
                    tour["destination_name"] = location["name"]
            elif "destination" in tour and isinstance(tour["destination"], list):
                # Xử lý trường hợp tour có nhiều điểm đến
                destination_names = []
                for dest_id in tour["destination"]:
                    if isinstance(dest_id, ObjectId):
                        location = db.locations.find_one({"_id": dest_id})
                        if location:
                            destination_names.append(location["name"])
                if destination_names:
                    tour["destination_names"] = destination_names
                    
        return tours
        
    def get_tour_by_id(self, tour_id):
        """Lấy thông tin chi tiết của một tour"""
        try:
            if isinstance(tour_id, str):
                tour_id = ObjectId(tour_id)
                
            tour = db.tours.find_one({"_id": tour_id})
            
            if not tour:
                return None
                
            # Thêm thông tin tên điểm đến
            if "destination" in tour and isinstance(tour["destination"], ObjectId):
                location = db.locations.find_one({"_id": tour["destination"]})
                if location:
                    tour["destination_name"] = location["name"]
                    
            return tour
        except Exception as e:
            print(f"Error getting tour by id: {e}")
            return None
            
    def get_recommended_tours(self, limit=5):
        """Lấy danh sách tour đề xuất"""
        # Lấy các tour có giá tốt nhất
        tours = list(db.tours.find().sort("price", 1).limit(limit))
        
        # Thêm thông tin tên điểm đến
        for tour in tours:
            if "destination" in tour and isinstance(tour["destination"], ObjectId):
                location = db.locations.find_one({"_id": tour["destination"]})
                if location:
                    tour["destination_name"] = location["name"]
                    
        return tours
        
    def format_tour_detail(self, tour):
        """Định dạng thông tin chi tiết tour thành tin nhắn văn bản"""
        if not tour:
            return "Không tìm thấy thông tin tour."
            
        message = f"🚌 {tour['name'].upper()}\n\n"
        
        if "destination_name" in tour:
            message += f"📍 Điểm đến: {tour['destination_name']}\n"
        elif "destination_names" in tour:
            message += f"📍 Điểm đến: {', '.join(tour['destination_names'])}\n"
            
        message += f"⏱️ Thời gian: {tour['duration']}\n"
        
        # Định dạng giá tiền
        price_formatted = "{:,.0f}".format(tour['price']).replace(",", ".")
        message += f"💰 Giá: {price_formatted} VNĐ/khách\n\n"
        
        # Thêm mô tả
        message += f"🌟 {tour['description']}\n\n"
        
        # Thêm lịch khởi hành
        if "departure_dates" in tour and tour["departure_dates"]:
            message += "🗓️ Lịch khởi hành:\n"
            for i, date in enumerate(tour["departure_dates"][:3], 1):
                if isinstance(date, datetime):
                    date_str = date.strftime("%d/%m/%Y")
                else:
                    date_str = str(date)
                message += f"{i}. {date_str}\n"
            message += "\n"
            
        # Thêm chi tiết dịch vụ bao gồm
        if "inclusions" in tour or tour["inclusions"]:
            message += "✅ Dịch vụ bao gồm:\n"
            for item in tour["inclusions"]:
                message += f"• {item}\n"
            message += "\n"
            
        # Thêm dịch vụ không bao gồm
        if "exclusions" in tour or tour["exclusions"]:
            message += "❌ Dịch vụ không bao gồm:\n"
            for item in tour["exclusions"]:
                message += f"• {item}\n"
            message += "\n"
            
        message += "📞 Để đặt tour này, hãy nhập 'đặt tour' hoặc liên hệ hotline 1900xxxx để được tư vấn chi tiết."
        
        return message
        
    def create_tour(self, tour_data):
        """Tạo tour mới"""
        try:
            result = db.tours.insert_one(tour_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating tour: {e}")
            return None
            
    def update_tour(self, tour_id, tour_data):
        """Cập nhật thông tin tour"""
        try:
            if isinstance(tour_id, str):
                tour_id = ObjectId(tour_id)
                
            result = db.tours.update_one(
                {"_id": tour_id},
                {"$set": tour_data}
            )
            
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating tour: {e}")
            return False
            
    def delete_tour(self, tour_id):
        """Xóa tour"""
        try:
            if isinstance(tour_id, str):
                tour_id = ObjectId(tour_id)
                
            result = db.tours.delete_one({"_id": tour_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting tour: {e}")
            return False

# Khởi tạo service
tour_service = TourService()

