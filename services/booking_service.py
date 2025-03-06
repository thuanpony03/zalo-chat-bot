from datetime import datetime
from bson import ObjectId
from services.database import db
from models.booking import Booking

class BookingService:
    def create_tour_booking(self, user_id, tour_id, user_info):
        """Tạo đặt tour mới"""
        try:
            # Lấy thông tin tour
            tour = db.tours.find_one({"_id": ObjectId(tour_id)})
            if not tour:
                return {
                    "success": False,
                    "message": "Không tìm thấy thông tin tour"
                }
            
            # Tính tổng tiền
            num_adults = user_info.get("num_adults", 1)
            num_children = user_info.get("num_children", 0)
            total_price = (num_adults * tour["price"]) + (num_children * tour["price"] * 0.5)  # Giả sử trẻ em = 50% giá người lớn
            
            # Tạo booking mới
            new_booking = Booking(
                user_id=user_id,
                service_type="tour",
                service_id=ObjectId(tour_id),
                user_name=user_info.get("user_name"),
                user_phone=user_info.get("user_phone"),
                travel_date=user_info.get("travel_date"),
                num_adults=num_adults,
                num_children=num_children,
                total_price=total_price,
                status="pending",
                payment_method=user_info.get("payment_method"),
                notes=user_info.get("notes")
            )
            
            # Lưu vào database
            result = db.bookings.insert_one(new_booking.to_dict())
            
            return {
                "success": True,
                "booking_id": str(result.inserted_id),
                "message": "Đặt tour thành công"
            }
            
        except Exception as e:
            print(f"Error creating booking: {e}")
            return {
                "success": False,
                "message": "Đã xảy ra lỗi khi đặt tour"
            }
    
    def create_visa_booking(self, user_id, visa_id, user_info):
        """Tạo đặt dịch vụ visa mới"""
        try:
            # Lấy thông tin visa
            visa = db.visas.find_one({"_id": ObjectId(visa_id)})
            if not visa:
                return {
                    "success": False,
                    "message": "Không tìm thấy thông tin dịch vụ visa"
                }
            
            # Tính tổng tiền
            num_persons = user_info.get("num_persons", 1)
            total_price = num_persons * visa["price"]
            
            # Tạo booking mới
            new_booking = Booking(
                user_id=user_id,
                service_type="visa",
                service_id=ObjectId(visa_id),
                user_name=user_info.get("user_name"),
                user_phone=user_info.get("user_phone"),
                num_adults=num_persons,
                num_children=0,
                total_price=total_price,
                status="pending",
                notes=user_info.get("notes")
            )
            
            # Lưu vào database
            result = db.bookings.insert_one(new_booking.to_dict())
            
            return {
                "success": True,
                "booking_id": str(result.inserted_id),
                "message": "Đặt dịch vụ visa thành công"
            }
            
        except Exception as e:
            print(f"Error creating visa booking: {e}")
            return {
                "success": False,
                "message": "Đã xảy ra lỗi khi đặt dịch vụ visa"
            }
    
    def create_flight_booking(self, user_id, flight_id, user_info):
        """Tạo đặt vé máy bay mới"""
        try:
            # Lấy thông tin chuyến bay
            flight = db.flights.find_one({"_id": ObjectId(flight_id)})
            if not flight:
                return {
                    "success": False,
                    "message": "Không tìm thấy thông tin chuyến bay"
                }
            
            # Tính tổng tiền
            num_adults = user_info.get("num_adults", 1)
            num_children = user_info.get("num_children", 0)
            total_price = (num_adults * flight["price"]) + (num_children * flight["price"] * 0.75)  # Giả sử trẻ em = 75% giá người lớn
            
            # Tạo booking mới
            new_booking = Booking(
                user_id=user_id,
                service_type="flight",
                service_id=ObjectId(flight_id),
                user_name=user_info.get("user_name"),
                user_phone=user_info.get("user_phone"),
                travel_date=flight["departure_time"],
                num_adults=num_adults,
                num_children=num_children,
                total_price=total_price,
                status="pending",
                payment_method=user_info.get("payment_method"),
                notes=user_info.get("notes")
            )
            
            # Lưu vào database
            result = db.bookings.insert_one(new_booking.to_dict())
            
            return {
                "success": True,
                "booking_id": str(result.inserted_id),
                "message": "Đặt vé máy bay thành công"
            }
            
        except Exception as e:
            print(f"Error creating flight booking: {e}")
            return {
                "success": False,
                "message": "Đã xảy ra lỗi khi đặt vé máy bay"
            }
    
    def get_user_bookings(self, user_id):
        """Lấy danh sách đặt dịch vụ của người dùng"""
        try:
            bookings = list(db.bookings.find({"user_id": user_id}).sort("booking_date", -1))
            
            # Thêm thông tin chi tiết về dịch vụ
            for booking in bookings:
                service_type = booking["service_type"]
                service_id = booking["service_id"]
                
                if service_type == "tour":
                    tour = db.tours.find_one({"_id": service_id})
                    if tour:
                        booking["service_name"] = tour["name"]
                        
                elif service_type == "visa":
                    visa = db.visas.find_one({"_id": service_id})
                    if visa:
                        booking["service_name"] = f"Visa {visa['country']} - {visa['visa_type']}"
                        
                elif service_type == "flight":
                    flight = db.flights.find_one({"_id": service_id})
                    if flight:
                        booking["service_name"] = f"{flight['airline']} {flight['flight_number']} ({flight['departure']} - {flight['destination']})"
            
            return {
                "success": True,
                "bookings": bookings,
                "message": f"Tìm thấy {len(bookings)} lịch đặt"
            }
            
        except Exception as e:
            print(f"Error getting user bookings: {e}")
            return {
                "success": False,
                "message": "Đã xảy ra lỗi khi lấy thông tin đặt dịch vụ"
            }
    
    def get_booking_details(self, booking_id):
        """Lấy thông tin chi tiết của một đặt dịch vụ"""
        try:
            booking = db.bookings.find_one({"_id": ObjectId(booking_id)})
            if not booking:
                return {
                    "success": False,
                    "message": "Không tìm thấy thông tin đặt dịch vụ"
                }
            
            service_type = booking["service_type"]
            service_id = booking["service_id"]
            
            # Lấy thông tin chi tiết của dịch vụ
            service_details = None
            
            if service_type == "tour":
                service_details = db.tours.find_one({"_id": service_id})
                
            elif service_type == "visa":
                service_details = db.visas.find_one({"_id": service_id})
                
            elif service_type == "flight":
                service_details = db.flights.find_one({"_id": service_id})
            
            return {
                "success": True,
                "booking": booking,
                "service_details": service_details
            }
            
        except Exception as e:
            print(f"Error getting booking details: {e}")
            return {
                "success": False,
                "message": "Đã xảy ra lỗi khi lấy thông tin chi tiết đặt dịch vụ"
            }
    
    def update_booking_status(self, booking_id, status, notes=None):
        """Cập nhật trạng thái đặt dịch vụ"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now()
            }
            
            if notes:
                update_data["notes"] = notes
                
            result = db.bookings.update_one(
                {"_id": ObjectId(booking_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                return {
                    "success": False,
                    "message": "Không tìm thấy đặt dịch vụ hoặc không có thay đổi"
                }
                
            return {
                "success": True,
                "message": f"Cập nhật trạng thái đặt dịch vụ thành công: {status}"
            }
            
        except Exception as e:
            print(f"Error updating booking status: {e}")
            return {
                "success": False,
                "message": "Đã xảy ra lỗi khi cập nhật trạng thái đặt dịch vụ"
            }
    
    def format_booking_message(self, booking, include_service_details=False):
        """Định dạng thông tin đặt dịch vụ thành tin nhắn văn bản"""
        service_type_mapping = {
            "tour": "Tour du lịch",
            "visa": "Dịch vụ visa",
            "flight": "Vé máy bay",
            "passport": "Dịch vụ hộ chiếu"
        }
        
        status_mapping = {
            "pending": "Đang chờ xác nhận",
            "confirmed": "Đã xác nhận",
            "paid": "Đã thanh toán",
            "cancelled": "Đã hủy",
            "completed": "Đã hoàn thành"
        }
        
        service_type = service_type_mapping.get(booking["service_type"], booking["service_type"])
        status = status_mapping.get(booking["status"], booking["status"])
        
        message = f"📋 THÔNG TIN ĐẶT {service_type.upper()}\n\n"
        
        if "service_name" in booking:
            message += f"🔖 {booking['service_name']}\n\n"
        
        message += f"👤 Khách hàng: {booking.get('user_name', 'Không có tên')}\n"
        message += f"📱 Số điện thoại: {booking.get('user_phone', 'Không có số điện thoại')}\n"
        
        if "travel_date" in booking and booking["travel_date"]:
            if isinstance(booking["travel_date"], datetime):
                travel_date_str = booking["travel_date"].strftime("%d/%m/%Y")
            else:
                travel_date_str = str(booking["travel_date"])
            message += f"🗓️ Ngày đi: {travel_date_str}\n"
        
        message += f"👥 Số người: {booking.get('num_adults', 1)} người lớn"
        if booking.get('num_children', 0) > 0:
            message += f", {booking['num_children']} trẻ em"
        message += "\n"
        
        message += f"💰 Tổng tiền: {'{:,.0f}'.format(booking.get('total_price', 0)).replace(',', '.')} VNĐ\n"
        message += f"🔄 Trạng thái: {status}\n"
        
        if "booking_date" in booking:
            if isinstance(booking["booking_date"], datetime):
                booking_date_str = booking["booking_date"].strftime("%d/%m/%Y %H:%M")
            else:
                booking_date_str = str(booking["booking_date"])
            message += f"📅 Ngày đặt: {booking_date_str}\n"
        
        if booking.get("notes"):
            message += f"\n📝 Ghi chú: {booking['notes']}\n"
        
        return message

# Khởi tạo service
booking_service = BookingService()