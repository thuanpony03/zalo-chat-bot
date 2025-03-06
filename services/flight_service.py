# Service for flight_service
# Created: 2025-03-04 23:44:55
# Author: thuanpony03

from datetime import datetime
from services.database import db

class FlightService:
    def search_flights(self, departure, destination, departure_date=None, class_type=None):
        """Tìm kiếm chuyến bay dựa trên các tiêu chí"""
        search_filter = {
            "departure": {"$regex": departure, "$options": "i"},
            "destination": {"$regex": destination, "$options": "i"}
        }
        
        if departure_date:
            # Định dạng ngày tháng thành datetime object để tìm kiếm
            try:
                if isinstance(departure_date, str):
                    date_formats = ["%d/%m/%Y", "%Y-%m-%d"]
                    parsed_date = None
                    for fmt in date_formats:
                        try:
                            parsed_date = datetime.strptime(departure_date, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if parsed_date:
                        # Tìm các chuyến bay có ngày khởi hành trong cùng ngày
                        next_day = datetime(parsed_date.year, parsed_date.month, parsed_date.day + 1)
                        search_filter["departure_time"] = {
                            "$gte": parsed_date,
                            "$lt": next_day
                        }
            except Exception as e:
                print(f"Error parsing date: {e}")
        
        if class_type:
            search_filter["class_type"] = {"$regex": class_type, "$options": "i"}
        
        flights = list(db.flights.find(search_filter).sort("price", 1))  # Sắp xếp theo giá tăng dần
        return flights
    
    def format_flight_message(self, flight):
        """Định dạng thông tin chuyến bay thành tin nhắn văn bản"""
        message = f"✈️ {flight['airline']} - {flight['flight_number']}\n\n"
        
        # Định dạng thời gian
        departure_time = flight["departure_time"]
        arrival_time = flight["arrival_time"]
        
        if isinstance(departure_time, datetime):
            dep_time_str = departure_time.strftime("%H:%M %d/%m/%Y")
        else:
            dep_time_str = str(departure_time)
            
        if isinstance(arrival_time, datetime):
            arr_time_str = arrival_time.strftime("%H:%M %d/%m/%Y")
        else:
            arr_time_str = str(arrival_time)
        
        message += f"🛫 {flight['departure']} - {dep_time_str}\n"
        message += f"🛬 {flight['destination']} - {arr_time_str}\n"
        message += f"💺 Hạng vé: {flight['class_type']}\n"
        message += f"💰 Giá: {'{:,.0f}'.format(flight['price']).replace(',', '.')} VNĐ\n"
        message += f"🧳 Hành lý: {flight['baggage_allowance']}\n"
        
        return message
    
    def format_flight_list_message(self, flights):
        """Định dạng danh sách chuyến bay thành tin nhắn văn bản"""
        if not flights:
            return "Không tìm thấy chuyến bay phù hợp với yêu cầu của bạn."
        
        message = f"✈️ TÌM THẤY {len(flights)} CHUYẾN BAY PHÙ HỢP\n\n"
        
        for i, flight in enumerate(flights[:5], 1):  # Lấy tối đa 5 chuyến bay
            # Định dạng thời gian
            departure_time = flight["departure_time"]
            if isinstance(departure_time, datetime):
                dep_time_str = departure_time.strftime("%H:%M %d/%m/%Y")
            else:
                dep_time_str = str(departure_time)
            
            message += f"{i}. {flight['airline']} ({flight['flight_number']})\n"
            message += f"   🛫 {flight['departure']} - {dep_time_str}\n"
            message += f"   💰 {'{:,.0f}'.format(flight['price']).replace(',', '.')} VNĐ - {flight['class_type']}\n\n"
        
        message += "Để xem chi tiết, vui lòng trả lời số thứ tự chuyến bay."
        
        return message

# Khởi tạo service
flight_service = FlightService()