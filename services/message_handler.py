from datetime import datetime
import json
from services.database import db
from services.nlp_processor import NLPProcessor
from services.tour_service import tour_service
from services.visa_service import visa_service
from services.passport_service import passport_service
from services.flight_service import flight_service
from services.booking_service import booking_service
from services.weather_service import weather_service

from services.ai_processor import ai_processor


class MessageHandler:
    def __init__(self):
        self.nlp = NLPProcessor()
    
    # Cập nhật trong message_handler.py
    async def process_message(self, user_id, message):
        """Xử lý tin nhắn từ người dùng"""
        try:
            # Lưu tin nhắn vào lịch sử trò chuyện
            self._save_message_to_history(user_id, "user", message)
            
            # Lấy context hiện tại và 3 tin nhắn gần nhất
            user_context = self._get_user_context(user_id) or {}
            recent_messages = self._get_recent_messages(user_id, limit=3)
            user_context["previous_messages"] = recent_messages
            
            # Phân tích cơ bản để lấy ý định và thực thể 
            analysis = self.nlp.analyze_message(message)
            intent = analysis["intent"]
            entities = analysis["entities"]
            
            # Cập nhật context người dùng
            user_context["intent"] = intent
            user_context["entities"] = entities
            self._update_user_context(user_id, user_context)
            
            # Cập nhật sở thích người dùng
            ai_processor.update_user_preferences(user_id, message, entities)
            
            # Kiểm tra nếu người dùng đang trong quá trình đặt dịch vụ
            if "booking_flow" in user_context and user_context["booking_flow"]["active"]:
                # Xử lý tin nhắn trong luồng đặt dịch vụ
                response = await self._process_booking_flow(user_id, message, user_context)

            # Add to the process_message method in MessageHandler
            if message.lower() in ["reset", "restart", "hủy", "reset context"]:
                self._update_user_context(user_id, {"booking_flow": None})
                return "Đã reset trạng thái hội thoại. Bạn có thể bắt đầu lại với một yêu cầu mới."
                
            # Nếu intent rõ ràng, sử dụng xử lý hiện tại
            elif intent != "UNKNOWN" and intent in ["TOUR_SEARCH", "VISA_INFO", "PASSPORT_INFO", 
                                            "FLIGHT_INFO", "BOOKING_ACTION", "BOOKING_STATUS"]:
                response = await self._process_by_intent(user_id, intent, entities, message)
            else:
                # Sử dụng Gemini AI cho các câu hỏi tự do và không rõ intent
                response = await ai_processor.generate_response(message, user_context)
            
            # Lưu phản hồi vào lịch sử trò chuyện
            self._save_message_to_history(user_id, "bot", response)
            
            return response
        except Exception as e:
            print(f"Error processing message: {e}")
            return "Xin lỗi, đã xảy ra lỗi khi xử lý tin nhắn của bạn. Vui lòng thử lại sau."

    # Thêm hàm mới để lấy lịch sử tin nhắn gần đây
    def _get_recent_messages(self, user_id, limit=3):
        """Lấy các tin nhắn gần đây của người dùng"""
        messages = list(db.conversations.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit))
        
        # Đảo ngược lại để có thứ tự thời gian đúng
        return list(reversed(messages))
    
    async def _process_by_intent(self, user_id, intent, entities, original_message):
        """Xử lý tin nhắn dựa trên ý định"""
        if intent == "TOUR_SEARCH":
            return await self._handle_tour_search(entities)
        
        elif intent == "VISA_INFO":
            return await self._handle_visa_info(entities, original_message)
        
        elif intent == "PASSPORT_INFO":
            return await self._handle_passport_info(original_message)
        
        elif intent == "FLIGHT_INFO":
            return await self._handle_flight_info(entities, original_message)
        
        elif intent == "WEATHER_INFO":
            return await self._handle_weather_info(entities)
        
        elif intent == "BOOKING_ACTION":
            return await self._handle_booking_action(user_id, entities, original_message)
        
        elif intent == "BOOKING_STATUS":
            return await self._handle_booking_status(user_id)
        
        elif intent == "FAQ":
            return await self._handle_faq(original_message)
        
        elif intent == "GREETING":
            return await self._handle_greeting(user_id)
        
        else:
            return "Xin lỗi, tôi không hiểu yêu cầu của bạn. Bạn có thể hỏi về tour du lịch, dịch vụ visa, hộ chiếu, vé máy bay, hoặc thông tin thời tiết."
    
    async def _handle_tour_search(self, entities):
        """Xử lý tìm kiếm tour du lịch"""
        # Nếu có địa điểm cụ thể
        if entities["locations"]:
            location = entities["locations"][0]
            tours = tour_service.search_tours(destination=location)
            
            if tours:
                response = f"🔍 TÌM THẤY {len(tours)} TOUR ĐẾN {location.upper()}\n\n"
                
                for i, tour in enumerate(tours[:5], 1):  # Giới hạn hiển thị 5 tour
                    response += f"{i}. {tour['name']}\n"
                    response += f"   ⏱️ {tour.get('duration', 'N/A')}\n"
                    formatted_price = "{:,.0f}".format(tour.get('price', 0)).replace(",", ".")
                    response += f"   💰 {formatted_price} VNĐ\n\n"
                
                response += "Để xem thông tin chi tiết của tour, vui lòng trả lời số thứ tự tương ứng."
                return response
            else:
                return f"Không tìm thấy tour nào đến {location}. Vui lòng thử tìm kiếm địa điểm khác."
        else:
            # Không có địa điểm cụ thể, đề xuất các tour phổ biến
            recommended_tours = tour_service.get_recommended_tours()
            
            if recommended_tours:
                response = "🌟 TOUR DU LỊCH ĐỀ XUẤT\n\n"
                
                for i, tour in enumerate(recommended_tours, 1):
                    response += f"{i}. {tour['name']}\n"
                    if "destination_name" in tour:
                        response += f"   📍 {tour['destination_name']}\n"
                    elif "destination_names" in tour:
                        response += f"   📍 {', '.join(tour['destination_names'])}\n"
                    response += f"   ⏱️ {tour.get('duration', 'N/A')}\n"
                    formatted_price = "{:,.0f}".format(tour.get('price', 0)).replace(",", ".")
                    response += f"   💰 {formatted_price} VNĐ\n\n"
                
                response += "Bạn có thể tìm kiếm tour đến địa điểm cụ thể bằng cách nhập 'tour + tên địa điểm', ví dụ: 'tour Nhật Bản'"
                return response
            else:
                return "Hiện tại chúng tôi chưa có tour nào. Vui lòng thử lại sau."
    
    async def _handle_visa_info(self, entities, original_message):
        """Xử lý thông tin visa"""
        # Sử dụng visa service để lấy và định dạng thông tin visa
        visa_info = visa_service.get_visa_info(original_message)
        
        if visa_info["success"]:
            return visa_service.format_visa_response(visa_info)
        else:
            return visa_info["message"]
    
    async def _handle_passport_info(self, original_message):
        """Xử lý thông tin hộ chiếu"""
        message_lower = original_message.lower()
        
        # Xác định loại dịch vụ hộ chiếu
        service_type = "new"  # Mặc định là làm hộ chiếu mới
        
        if "gia hạn" in message_lower or "extend" in message_lower:
            service_type = "extend"
        elif "cấp lại" in message_lower or "replace" in message_lower or "mất" in message_lower:
            service_type = "replace"
        
        # Lấy thông tin dịch vụ hộ chiếu
        passport_info = passport_service.get_passport_info(service_type)
        
        if passport_info:
            return passport_service.format_passport_info_message(passport_info)
        else:
            return "Xin lỗi, hiện tại chúng tôi chưa có thông tin về dịch vụ hộ chiếu này. Vui lòng liên hệ trực tiếp với chúng tôi để được tư vấn chi tiết."
    
    async def _handle_flight_info(self, entities, original_message):
        """Xử lý thông tin vé máy bay"""
        message_lower = original_message.lower()
        
        # Tìm điểm khởi hành và điểm đến
        departure = None
        destination = None
        
        # Danh sách các thành phố/quốc gia phổ biến
        common_cities = ["hà nội", "hồ chí minh", "đà nẵng", "nha trang", "phú quốc", 
                        "tokyo", "osaka", "seoul", "bangkok", "singapore", "hong kong", 
                        "beijing", "sydney", "new york", "paris", "london"]
        
        # Thử tìm các thành phố trong tin nhắn
        found_cities = []
        for city in common_cities:
            if city in message_lower:
                found_cities.append(city)
        
        if len(found_cities) >= 2:
            departure = found_cities[0]
            destination = found_cities[1]
        elif len(found_cities) == 1:
            # Nếu chỉ tìm thấy một thành phố, giả định đó là điểm đến
            destination = found_cities[0]
            # Mặc định là Hà Nội hoặc TP.HCM
            departure = "hà nội" if destination != "hà nội" else "hồ chí minh"
        
        if departure and destination:
            # Tìm thông tin chuyến bay
            flights = flight_service.search_flights(departure, destination)
            
            if flights:
                return flight_service.format_flight_list_message(flights)
            else:
                return f"Xin lỗi, hiện tại chúng tôi không tìm thấy chuyến bay nào từ {departure} đến {destination}. Vui lòng thử lại với các điểm khác hoặc liên hệ với chúng tôi để được hỗ trợ."
        else:
            return "Vui lòng cho biết điểm khởi hành và điểm đến để tìm kiếm vé máy bay. Ví dụ: 'Tìm vé máy bay từ Hà Nội đi Tokyo'"
    
    async def _handle_weather_info(self, entities):
        """Xử lý thông tin thời tiết"""
        if entities["locations"]:
            location = entities["locations"][0]
            weather_info = await weather_service.get_weather(location)
            
            if weather_info:
                return weather_service.format_weather_message(weather_info)
            else:
                return f"Xin lỗi, không tìm thấy thông tin thời tiết cho {location}."
        else:
            return "Vui lòng cho biết địa điểm bạn muốn xem thông tin thời tiết. Ví dụ: 'Thời tiết ở Tokyo'"
    
    async def _handle_booking_action(self, user_id, entities, original_message):
        """Khởi đầu quy trình đặt dịch vụ"""
        message_lower = original_message.lower()
        
        booking_type = None
        if "tour" in message_lower:
            booking_type = "tour"
        elif "visa" in message_lower:
            booking_type = "visa"
        elif "vé máy bay" in message_lower or "chuyến bay" in message_lower:
            booking_type = "flight"
        
        if not booking_type:
            return "Bạn muốn đặt dịch vụ gì? Tour du lịch, visa hay vé máy bay?"
        
        # Khởi tạo luồng đặt dịch vụ
        booking_flow = {
            "active": True,
            "type": booking_type,
            "step": "init",
            "data": {}
        }
        
        self._update_user_context(user_id, {"booking_flow": booking_flow})
        
        if booking_type == "tour":
            return "🚌 ĐẶT TOUR DU LỊCH\n\nVui lòng cho biết bạn muốn đặt tour đi đâu? (Ví dụ: Nhật Bản, Hàn Quốc, Châu Âu, ...)"
        elif booking_type == "visa":
            return "🛂 ĐẶT DỊCH VỤ VISA\n\nVui lòng cho biết bạn muốn làm visa nước nào? (Ví dụ: Nhật Bản, Mỹ, Châu Âu, ...)"
        elif booking_type == "flight":
            return "✈️ ĐẶT VÉ MÁY BAY\n\nVui lòng cho biết điểm khởi hành và điểm đến của bạn? (Ví dụ: Từ Hà Nội đi Tokyo)"
    
    async def _handle_booking_status(self, user_id):
        """Xử lý kiểm tra trạng thái đặt dịch vụ"""
        result = booking_service.get_user_bookings(user_id)
        
        if result["success"]:
            bookings = result["bookings"]
            
            if not bookings:
                return "Bạn chưa có đặt dịch vụ nào. Bạn có thể đặt tour du lịch, dịch vụ visa hoặc vé máy bay."
            
            response = f"📋 DANH SÁCH ĐẶT DỊCH VỤ CỦA BẠN ({len(bookings)})\n\n"
            
            for i, booking in enumerate(bookings[:5], 1):  # Giới hạn hiển thị 5 đặt dịch vụ
                service_type_mapping = {
                    "tour": "Tour",
                    "visa": "Visa",
                    "flight": "Vé máy bay"
                }
                service_type = service_type_mapping.get(booking["service_type"], booking["service_type"])
                
                status_mapping = {
                    "pending": "🕒 Đang chờ xác nhận",
                    "confirmed": "✅ Đã xác nhận",
                    "paid": "💲 Đã thanh toán",
                    "cancelled": "❌ Đã hủy",
                    "completed": "🏁 Đã hoàn thành"
                }
                status = status_mapping.get(booking["status"], booking["status"])
                
                response += f"{i}. {service_type}: "
                if "service_name" in booking:
                    response += f"{booking['service_name']}\n"
                else:
                    response += "\n"
                
                response += f"   {status}\n"
                
                if "booking_date" in booking:
                    if isinstance(booking["booking_date"], datetime):
                        booking_date_str = booking["booking_date"].strftime("%d/%m/%Y")
                    else:
                        booking_date_str = str(booking["booking_date"])
                    response += f"   📅 Ngày đặt: {booking_date_str}\n"
                
                response += "\n"
            
            response += "Để xem chi tiết, hãy trả lời với số thứ tự tương ứng."
            return response
        else:
            return "Xin lỗi, không thể lấy thông tin đặt dịch vụ của bạn. Vui lòng thử lại sau."
    
    async def _handle_greeting(self, user_id):
        """Xử lý lời chào"""
        return "👋 Xin chào! Tôi là chatbot du lịch của Passport Lounge. Tôi có thể giúp bạn:\n\n" + \
               "1️⃣ Tìm kiếm tour du lịch nước ngoài\n" + \
               "2️⃣ Cung cấp thông tin về thủ tục visa\n" + \
               "3️⃣ Hướng dẫn làm hộ chiếu\n" + \
               "4️⃣ Tìm kiếm và đặt vé máy bay\n" + \
               "5️⃣ Kiểm tra thời tiết tại điểm du lịch\n\n" + \
               "Bạn cần hỗ trợ gì hôm nay?"
    

    # Find the duplicate _handle_faq method implementations and replace them with this:

    async def _handle_faq(self, original_message):
        """Xử lý câu hỏi thường gặp"""
        message_lower = original_message.lower()
        
        # Tra cứu câu hỏi từ database
        keywords = message_lower.split()
        search_query = {"$or": []}
        
        for keyword in keywords:
            if len(keyword) > 3:  # Chỉ xét từ khóa có độ dài > 3
                search_query["$or"].append({"question": {"$regex": keyword, "$options": "i"}})
        
        faq = None
        if search_query["$or"]:
            faq = db.faqs.find_one(search_query)
        
        if faq:
            return f"❓ {faq['question']}\n\n✅ {faq['answer']}"
        else:
            # Một số câu hỏi thường gặp và câu trả lời
            faqs = {
                "thời gian làm visa": "⏱️ Thời gian làm visa tùy thuộc vào từng quốc gia:\n- Nhật Bản: 5-7 ngày làm việc\n- Hàn Quốc: 7-10 ngày làm việc\n- Mỹ: 2-4 tuần\n- Châu Âu (Schengen): 10-15 ngày làm việc",
                "hộ chiếu cần gì": "📚 Để làm hộ chiếu mới, bạn cần:\n1. Tờ khai đề nghị cấp hộ chiếu (mẫu X01)\n2. CMND/CCCD bản gốc\n3. 2 ảnh 4x6cm nền trắng\n4. Lệ phí: 200.000đ/quyển thông thường",
                "mang gì khi đi du lịch": "🧳 Những vật dụng cần thiết khi đi du lịch nước ngoài:\n1. Hộ chiếu và visa (còn hạn ít nhất 6 tháng)\n2. Bản sao giấy tờ quan trọng\n3. Tiền mặt và thẻ thanh toán quốc tế\n4. Quần áo phù hợp với thời tiết\n5. Adapter sạc điện\n6. Thuốc cá nhân\n7. Bảo hiểm du lịch",
                "đổi tiền": "💱 Bạn có thể đổi ngoại tệ tại ngân hàng hoặc các điểm thu đổi ngoại tệ được cấp phép. Chúng tôi khuyên bạn nên đổi một phần tiền trước khi đi và mang theo thẻ ATM quốc tế.",
                "bảo hiểm du lịch": "🏥 Bảo hiểm du lịch rất quan trọng, bao gồm chi phí y tế, mất hành lý, chuyến bay bị hoãn/hủy. Giá thường từ 200-500K cho 7-15 ngày tùy gói và quốc gia.",
                "hoàn/hủy tour": "↩️ Chính sách hoàn/hủy tour:\n- Hủy trước 30 ngày: hoàn 90% tổng giá trị\n- Hủy trước 15-29 ngày: hoàn 70% tổng giá trị\n- Hủy trước 7-14 ngày: hoàn 50% tổng giá trị\n- Hủy trước 1-6 ngày: hoàn 30% tổng giá trị\n- Ngày khởi hành: không hoàn tiền",
                "thanh toán": "💳 Chúng tôi chấp nhận các hình thức thanh toán:\n- Tiền mặt tại văn phòng\n- Chuyển khoản ngân hàng\n- Thẻ tín dụng/ghi nợ\n- Ví điện tử (Momo, ZaloPay, VNPay)"
            }
            
            for key, value in faqs.items():
                if key in message_lower:
                    return value
            
            # Nếu không tìm thấy câu hỏi phù hợp
            return "Xin lỗi, tôi không tìm thấy thông tin về câu hỏi của bạn. Vui lòng liên hệ hotline 1900xxxx để được tư vấn trực tiếp."

    
    async def _process_booking_flow(self, user_id, message, user_context):
        """Xử lý tin nhắn trong quy trình đặt dịch vụ"""
        booking_flow = user_context["booking_flow"]
        booking_type = booking_flow["type"]
        current_step = booking_flow["step"]
        booking_data = booking_flow["data"]
        
        # Xử lý hủy đặt dịch vụ
        if message.lower() in ["hủy", "cancel", "dừng", "stop", "quit"]:
            await self._update_user_context(user_id, {"booking_flow": None})
            return "Bạn đã hủy quá trình đặt dịch vụ. Bạn có thể bắt đầu lại khi cần."
        
        # Xử lý các bước đặt tour
        if booking_type == "tour":
            return await self._process_tour_booking_flow(user_id, message, current_step, booking_data)
        
        # Xử lý các bước đặt visa
        elif booking_type == "visa":
            return await self._process_visa_booking_flow(user_id, message, current_step, booking_data)
        
        # Xử lý các bước đặt vé máy bay
        elif booking_type == "flight":
            return await self._process_flight_booking_flow(user_id, message, current_step, booking_data)
    
    async def _process_tour_booking_flow(self, user_id, message, current_step, booking_data):
        """Xử lý các bước đặt tour"""
        next_step = current_step
        response = ""
        
        if current_step == "init":
            # Người dùng nhập địa điểm để tìm tour
            destination = message
            tours = tour_service.search_tours(destination=destination)
            
            if not tours:
                return f"Xin lỗi, chúng tôi không tìm thấy tour nào đến {destination}. Vui lòng thử lại với địa điểm khác."
            
            booking_data["tours"] = tours
            booking_data["destination"] = destination
            
            response = f"🔍 TÌM THẤY {len(tours)} TOUR ĐẾN {destination.upper()}\n\n"
            
            for i, tour in enumerate(tours[:5], 1):  # Giới hạn hiển thị 5 tour
                response += f"{i}. {tour['name']}\n"
                response += f"   ⏱️ {tour.get('duration', 'N/A')}\n"
                formatted_price = "{:,.0f}".format(tour.get('price', 0)).replace(",", ".")
                response += f"   💰 {formatted_price} VNĐ\n\n"
            
            response += "Vui lòng chọn số thứ tự tour bạn muốn đặt."
            next_step = "select_tour"
        
        elif current_step == "select_tour":
            # Người dùng chọn tour
            try:
                tour_index = int(message) - 1
                tours = booking_data["tours"]
                
                if tour_index < 0 or tour_index >= len(tours):
                    return "Vui lòng chọn một số từ danh sách tour."
                
                selected_tour = tours[tour_index]
                booking_data["selected_tour"] = selected_tour
                
                response = f"🚌 Bạn đã chọn: {selected_tour['name']}\n\n"
                response += f"Vui lòng nhập họ và tên đầy đủ của bạn."
                next_step = "input_name"
                
            except ValueError:
                return "Vui lòng nhập số thứ tự tour (ví dụ: 1, 2, 3...)"
        
        elif current_step == "input_name":
            # Người dùng nhập họ tên
            booking_data["user_name"] = message
            
            response = f"Cảm ơn {message}. Vui lòng nhập số điện thoại liên hệ của bạn."
            next_step = "input_phone"
        
        elif current_step == "input_phone":
            # Người dùng nhập số điện thoại
            # Kiểm tra định dạng số điện thoại
            import re
            phone_pattern = re.compile(r"^(0|\+84)\d{9,10}$")
            
            if not phone_pattern.match(message):
                return "Số điện thoại không hợp lệ. Vui lòng nhập lại (ví dụ: 0912345678 hoặc +84912345678)."
            
            booking_data["user_phone"] = message
            
            response = "Vui lòng nhập ngày bạn muốn khởi hành theo định dạng DD/MM/YYYY (ví dụ: 15/06/2025)."
            next_step = "input_date"
        
        elif current_step == "input_date":
            # Người dùng nhập ngày khởi hành
            import re
            from datetime import datetime
            
            date_pattern = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")
            match = date_pattern.match(message)
            
            if not match:
                return "Định dạng ngày không hợp lệ. Vui lòng nhập lại theo định dạng DD/MM/YYYY (ví dụ: 15/06/2025)."
            
            day, month, year = map(int, match.groups())
            
            try:
                travel_date = datetime(year, month, day)
                current_date = datetime.now()
                
                if travel_date <= current_date:
                    return "Ngày khởi hành phải sau ngày hiện tại. Vui lòng nhập lại."
                
                booking_data["travel_date"] = travel_date
                
                response = "Vui lòng nhập số lượng người tham gia tour (ví dụ: 2 người lớn, 1 trẻ em)."
                next_step = "input_people"
                
            except ValueError:
                return "Ngày không hợp lệ. Vui lòng nhập lại theo định dạng DD/MM/YYYY (ví dụ: 15/06/2025)."
        
        elif current_step == "input_people":
            # Người dùng nhập số lượng người tham gia
            import re
            
            people_pattern = re.compile(r"(\d+)\s*(?:người lớn|người|adults)(?:,?\s*(\d+)\s*(?:trẻ em|children|kids))?", re.IGNORECASE)
            match = people_pattern.match(message)
            
            if not match:
                return "Vui lòng nhập số lượng người tham gia theo định dạng: [số người lớn] người lớn, [số trẻ em] trẻ em (ví dụ: 2 người lớn, 1 trẻ em)."
            
            adults = int(match.group(1))
            children = int(match.group(2)) if match.group(2) else 0
            
            booking_data["num_adults"] = adults
            booking_data["num_children"] = children
            
            # Tính tổng tiền
            tour_price = booking_data["selected_tour"]["price"]
            total_price = (adults * tour_price) + (children * tour_price * 0.5)  # Giả sử trẻ em = 50% giá người lớn
            booking_data["total_price"] = total_price
            
            # Hiển thị thông tin xác nhận
            response = "📋 XÁC NHẬN ĐẶT TOUR\n\n"
            response += f"🚌 Tour: {booking_data['selected_tour']['name']}\n"
            response += f"👤 Họ tên: {booking_data['user_name']}\n"
            response += f"📱 Số điện thoại: {booking_data['user_phone']}\n"
            
            travel_date = booking_data["travel_date"]
            response += f"🗓️ Ngày khởi hành: {travel_date.strftime('%d/%m/%Y')}\n"
            
            response += f"👥 Số người: {adults} người lớn"
            if children > 0:
                response += f", {children} trẻ em"
            response += "\n"
            
            formatted_price = "{:,.0f}".format(total_price).replace(",", ".")
            response += f"💰 Tổng tiền: {formatted_price} VNĐ\n\n"
            
            response += "Vui lòng xác nhận đặt tour bằng cách nhập 'xác nhận' hoặc 'hủy' để hủy đặt tour."
            next_step = "confirm"
        
        elif current_step == "confirm":
            # Người dùng xác nhận đặt tour
            if message.lower() in ["xác nhận", "đồng ý", "ok", "confirm", "yes"]:
                # Lưu đặt tour vào database
                result = booking_service.create_tour_booking(
                    user_id=user_id,
                    tour_id=booking_data["selected_tour"]["_id"],
                    user_info={
                        "user_name": booking_data["user_name"],
                        "user_phone": booking_data["user_phone"],
                        "travel_date": booking_data["travel_date"],
                        "num_adults": booking_data["num_adults"],
                        "num_children": booking_data.get("num_children", 0)
                    }
                )
                
                if result["success"]:
                    response = "🎉 ĐẶT TOUR THÀNH CÔNG!\n\n"
                    response += f"Mã đặt tour của bạn là: #{result['booking_id']}\n\n"
                    response += "Nhân viên của Thuận Pony Travel sẽ liên hệ với bạn trong vòng 24 giờ để xác nhận chi tiết và hướng dẫn thanh toán.\n\n"
                    response += "Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi! 😊"
                else:
                    response = f"❌ Rất tiếc, đã xảy ra lỗi khi đặt tour: {result['message']}\n"
                    response += "Vui lòng thử lại sau hoặc liên hệ trực tiếp với chúng tôi qua hotline 1900xxxx để được hỗ trợ."
            else:
                response = "Bạn đã hủy đặt tour. Bạn có thể bắt đầu lại khi cần."
            
            # Kết thúc luồng đặt tour
            await self._update_user_context(user_id, {"booking_flow": None})
            return response
        
        # Cập nhật thông tin đặt tour
        await self._update_user_context(user_id, {
            "booking_flow": {
                "active": True,
                "type": "tour",
                "step": next_step,
                "data": booking_data
            }
        })
        
        return response
    
    async def _process_visa_booking_flow(self, user_id, message, current_step, booking_data):
        """Xử lý các bước đặt dịch vụ visa"""
        next_step = current_step
        response = ""
        
        if current_step == "init":
            # Người dùng nhập quốc gia cần làm visa
            country = message
            visa_infos = visa_service.search_visa_info(country=country)
            
            if not visa_infos:
                return f"Xin lỗi, chúng tôi không tìm thấy thông tin visa cho {country}. Vui lòng thử lại với quốc gia khác hoặc liên hệ trực tiếp với chúng tôi."
            
            booking_data["visa_infos"] = visa_infos
            booking_data["country"] = country
            
            if len(visa_infos) == 1:
                # Nếu chỉ có 1 loại visa
                booking_data["selected_visa"] = visa_infos[0]
                
                response = visa_service.format_visa_info_message(visa_infos[0])
                response += "\n\nBạn có muốn đặt dịch vụ visa này không? (Có/Không)"
                next_step = "confirm_visa_type"
            else:
                # Nếu có nhiều loại visa
                response = f"🔍 TÌM THẤY {len(visa_infos)} LOẠI VISA CHO {country.upper()}\n\n"
                
                for i, visa in enumerate(visa_infos, 1):
                    response += f"{i}. Visa {visa['visa_type']}\n"
                    response += f"   ⏱️ Thời gian xử lý: {visa['processing_time']}\n"
                    formatted_price = "{:,.0f}".format(visa['price']).replace(",", ".")
                    response += f"   💰 Phí: {formatted_price} VNĐ\n\n"
                
                response += "Vui lòng chọn số thứ tự loại visa bạn muốn đặt."
                next_step = "select_visa_type"
        
        elif current_step == "select_visa_type":
            # Người dùng chọn loại visa
            try:
                visa_index = int(message) - 1
                visa_infos = booking_data["visa_infos"]
                
                if visa_index < 0 or visa_index >= len(visa_infos):
                    return "Vui lòng chọn một số từ danh sách visa."
                
                selected_visa = visa_infos[visa_index]
                booking_data["selected_visa"] = selected_visa
                
                response = visa_service.format_visa_info_message(selected_visa)
                response += "\n\nBạn có muốn đặt dịch vụ visa này không? (Có/Không)"
                next_step = "confirm_visa_type"
                
            except ValueError:
                return "Vui lòng nhập số thứ tự visa (ví dụ: 1, 2, 3...)"
        
        elif current_step == "confirm_visa_type":
            # Người dùng xác nhận loại visa
            if message.lower() in ["có", "ok", "yes", "đồng ý", "xác nhận", "y"]:
                response = "Vui lòng nhập họ và tên đầy đủ của bạn."
                next_step = "input_name"
            else:
                await self._update_user_context(user_id, {"booking_flow": None})
                return "Bạn đã hủy đặt dịch vụ visa. Bạn có thể bắt đầu lại khi cần."
        
        elif current_step == "input_name":
            # Người dùng nhập họ tên
            booking_data["user_name"] = message
            
            response = f"Cảm ơn {message}. Vui lòng nhập số điện thoại liên hệ của bạn."
            next_step = "input_phone"
        
        elif current_step == "input_phone":
            # Người dùng nhập số điện thoại
            import re
            phone_pattern = re.compile(r"^(0|\+84)\d{9,10}$")
            
            if not phone_pattern.match(message):
                return "Số điện thoại không hợp lệ. Vui lòng nhập lại (ví dụ: 0912345678 hoặc +84912345678)."
            
            booking_data["user_phone"] = message
            
            response = "Vui lòng nhập số người cần làm visa."
            next_step = "input_persons"
        
        elif current_step == "input_persons":
            # Người dùng nhập số người cần làm visa
            try:
                num_persons = int(message)
                
                if num_persons <= 0:
                    return "Số người không hợp lệ. Vui lòng nhập lại."
                
                booking_data["num_persons"] = num_persons
                
                # Tính tổng tiền
                visa_price = booking_data["selected_visa"]["price"]
                total_price = num_persons * visa_price
                booking_data["total_price"] = total_price
                
                # Hiển thị thông tin xác nhận
                response = "📋 XÁC NHẬN ĐẶT DỊCH VỤ VISA\n\n"
                response += f"🛂 Loại visa: {booking_data['selected_visa']['visa_type']} - {booking_data['country']}\n"
                response += f"👤 Họ tên: {booking_data['user_name']}\n"
                response += f"📱 Số điện thoại: {booking_data['user_phone']}\n"
                response += f"👥 Số người: {num_persons}\n"
                
                formatted_price = "{:,.0f}".format(total_price).replace(",", ".")
                response += f"💰 Tổng phí: {formatted_price} VNĐ\n"
                response += f"⏱️ Thời gian xử lý: {booking_data['selected_visa']['processing_time']}\n\n"
                
                response += "Vui lòng xác nhận đặt dịch vụ visa bằng cách nhập 'xác nhận' hoặc 'hủy' để hủy."
                next_step = "confirm"
                
            except ValueError:
                return "Vui lòng nhập số người bằng chữ số (ví dụ: 2)."
        
        elif current_step == "confirm":
            # Người dùng xác nhận đặt dịch vụ visa
            if message.lower() in ["xác nhận", "đồng ý", "ok", "confirm", "yes"]:
                # Lưu đặt dịch vụ visa vào database
                result = booking_service.create_visa_booking(
                    user_id=user_id,
                    visa_id=booking_data["selected_visa"]["_id"],
                    user_info={
                        "user_name": booking_data["user_name"],
                        "user_phone": booking_data["user_phone"],
                        "num_persons": booking_data["num_persons"]
                    }
                )
                
                if result["success"]:
                    response = "🎉 ĐẶT DỊCH VỤ VISA THÀNH CÔNG!\n\n"
                    response += f"Mã đặt dịch vụ của bạn là: #{result['booking_id']}\n\n"
                    response += "Nhân viên của Thuận Pony Travel sẽ liên hệ với bạn trong vòng 24 giờ để hướng dẫn chuẩn bị hồ sơ và thanh toán.\n\n"
                    response += "Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi! 😊"
                else:
                    response = f"❌ Rất tiếc, đã xảy ra lỗi khi đặt dịch vụ visa: {result['message']}\n"
                    response += "Vui lòng thử lại sau hoặc liên hệ trực tiếp với chúng tôi qua hotline 1900xxxx để được hỗ trợ."
            else:
                response = "Bạn đã hủy đặt dịch vụ visa. Bạn có thể bắt đầu lại khi cần."
            
            # Kết thúc luồng đặt visa
            await self._update_user_context(user_id, {"booking_flow": None})
            return response
        
        # Cập nhật thông tin đặt visa
        await self._update_user_context(user_id, {
            "booking_flow": {
                "active": True,
                "type": "visa",
                "step": next_step,
                "data": booking_data
            }
        })
        
        return response
    
    async def _process_flight_booking_flow(self, user_id, message, current_step, booking_data):
        """Xử lý các bước đặt vé máy bay"""
        next_step = current_step
        response = ""
        
        if current_step == "init":
            # Người dùng nhập điểm đi và điểm đến
            message_lower = message.lower()
            # Tìm điểm khởi hành và điểm đến
            departure = None
            destination = None
            
            # Danh sách các thành phố/quốc gia phổ biến
            common_cities = ["hà nội", "hồ chí minh", "đà nẵng", "nha trang", "phú quốc", 
                            "tokyo", "osaka", "seoul", "bangkok", "singapore", "hong kong", 
                            "beijing", "sydney", "new york", "paris", "london"]
            
            # Thử tìm các thành phố trong tin nhắn
            found_cities = []
            for city in common_cities:
                if city in message_lower:
                    found_cities.append(city)
            
            if len(found_cities) >= 2:
                departure = found_cities[0]
                destination = found_cities[1]
                booking_data["departure"] = departure
                booking_data["destination"] = destination
                
                # Tìm các chuyến bay phù hợp
                flights = flight_service.search_flights(departure, destination)
                
                if not flights:
                    return f"Xin lỗi, chúng tôi không tìm thấy chuyến bay nào từ {departure} đến {destination}. Vui lòng thử lại với các điểm khác."
                
                booking_data["flights"] = flights
                
                response = flight_service.format_flight_list_message(flights)
                next_step = "select_flight"
            else:
                return "Vui lòng nhập rõ điểm đi và điểm đến (ví dụ: từ Hà Nội đến Tokyo)."
        
        elif current_step == "select_flight":
            # Người dùng chọn chuyến bay
            try:
                flight_index = int(message) - 1
                flights = booking_data["flights"]
                
                if flight_index < 0 or flight_index >= len(flights):
                    return "Vui lòng chọn một số từ danh sách chuyến bay."
                
                selected_flight = flights[flight_index]
                booking_data["selected_flight"] = selected_flight
                
                response = flight_service.format_flight_message(selected_flight)
                response += "\n\nBạn có muốn đặt vé chuyến bay này không? (Có/Không)"
                next_step = "confirm_flight"
                
            except ValueError:
                return "Vui lòng nhập số thứ tự chuyến bay (ví dụ: 1, 2, 3...)"
        
        elif current_step == "confirm_flight":
            # Người dùng xác nhận chuyến bay
            if message.lower() in ["có", "ok", "yes", "đồng ý", "xác nhận", "y"]:
                response = "Vui lòng nhập họ và tên đầy đủ của bạn."
                next_step = "input_name"
            else:
                await self._update_user_context(user_id, {"booking_flow": None})
                return "Bạn đã hủy đặt vé máy bay. Bạn có thể bắt đầu lại khi cần."
        
        elif current_step == "input_name":
            # Người dùng nhập họ tên
            booking_data["user_name"] = message
            
            response = f"Cảm ơn {message}. Vui lòng nhập số điện thoại liên hệ của bạn."
            next_step = "input_phone"
        
        elif current_step == "input_phone":
            # Người dùng nhập số điện thoại
            import re
            phone_pattern = re.compile(r"^(0|\+84)\d{9,10}$")
            
            if not phone_pattern.match(message):
                return "Số điện thoại không hợp lệ. Vui lòng nhập lại (ví dụ: 0912345678 hoặc +84912345678)."
            
            booking_data["user_phone"] = message
            
            response = "Vui lòng nhập số lượng hành khách (ví dụ: 2 người lớn, 1 trẻ em)."
            next_step = "input_passengers"
        
        elif current_step == "input_passengers":
            # Người dùng nhập số lượng hành khách
            import re
            
            people_pattern = re.compile(r"(\d+)\s*(?:người lớn|người|adults)(?:,?\s*(\d+)\s*(?:trẻ em|children|kids))?", re.IGNORECASE)
            match = people_pattern.match(message)
            
            if not match:
                return "Vui lòng nhập số lượng hành khách theo định dạng: [số người lớn] người lớn, [số trẻ em] trẻ em (ví dụ: 2 người lớn, 1 trẻ em)."
            
            adults = int(match.group(1))
            children = int(match.group(2)) if match.group(2) else 0
            
            booking_data["num_adults"] = adults
            booking_data["num_children"] = children
            
            # Tính tổng tiền
            flight_price = booking_data["selected_flight"]["price"]
            total_price = (adults * flight_price) + (children * flight_price * 0.75)  # Giả sử trẻ em = 75% giá người lớn
            booking_data["total_price"] = total_price
            
            # Hiển thị thông tin xác nhận
            flight = booking_data["selected_flight"]
            response = "📋 XÁC NHẬN ĐẶT VÉ MÁY BAY\n\n"
            response += f"✈️ Chuyến bay: {flight['airline']} {flight['flight_number']}\n"
            
            # Định dạng thời gian
            departure_time = flight["departure_time"]
            if isinstance(departure_time, datetime):
                dep_time_str = departure_time.strftime("%H:%M %d/%m/%Y")
            else:
                dep_time_str = str(departure_time)
            
            response += f"🛫 {flight['departure']} - {dep_time_str}\n"
            response += f"🛬 {flight['destination']}\n"
            response += f"💺 Hạng vé: {flight['class_type']}\n"
            response += f"👤 Họ tên: {booking_data['user_name']}\n"
            response += f"📱 Số điện thoại: {booking_data['user_phone']}\n"
            
            response += f"👥 Số hành khách: {adults} người lớn"
            if children > 0:
                response += f", {children} trẻ em"
            response += "\n"
            
            formatted_price = "{:,.0f}".format(total_price).replace(",", ".")
            response += f"💰 Tổng tiền: {formatted_price} VNĐ\n\n"
            
            response += "Vui lòng xác nhận đặt vé bằng cách nhập 'xác nhận' hoặc 'hủy' để hủy đặt vé."
            next_step = "confirm"
        
        elif current_step == "confirm":
            # Người dùng xác nhận đặt vé
            if message.lower() in ["xác nhận", "đồng ý", "ok", "confirm", "yes"]:
                # Lưu đặt vé vào database
                result = booking_service.create_flight_booking(
                    user_id=user_id,
                    flight_id=booking_data["selected_flight"]["_id"],
                    user_info={
                        "user_name": booking_data["user_name"],
                        "user_phone": booking_data["user_phone"],
                        "num_adults": booking_data["num_adults"],
                        "num_children": booking_data.get("num_children", 0)
                    }
                )
                
                if result["success"]:
                    response = "🎉 ĐẶT VÉ MÁY BAY THÀNH CÔNG!\n\n"
                    response += f"Mã đặt vé của bạn là: #{result['booking_id']}\n\n"
                    response += "Nhân viên của Thuận Pony Travel sẽ liên hệ với bạn trong vòng 24 giờ để xác nhận chi tiết và hướng dẫn thanh toán.\n\n"
                    response += "Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi! 😊"
                else:
                    response = f"❌ Rất tiếc, đã xảy ra lỗi khi đặt vé: {result['message']}\n"
                    response += "Vui lòng thử lại sau hoặc liên hệ trực tiếp với chúng tôi qua hotline 1900xxxx để được hỗ trợ."
            else:
                response = "Bạn đã hủy đặt vé máy bay. Bạn có thể bắt đầu lại khi cần."
            
            # Kết thúc luồng đặt vé
            await self._update_user_context(user_id, {"booking_flow": None})
            return response
        
        # Cập nhật thông tin đặt vé
        def _update_user_context(self, user_id, context_update):
            """Cập nhật context của người dùng (synchronous version)"""
            result = db.users.update_one(
                {"user_id": user_id},
                {"$set": {"context": context_update}},
                upsert=True
            )
            return result
        
        return response
    
    def _save_message_to_history(self, user_id, sender_type, message):
        """Lưu tin nhắn vào lịch sử trò chuyện (synchronous version)"""
        message_data = {
            "user_id": user_id,
            "sender": sender_type,  # "user" hoặc "bot"
            "message": message,
            "timestamp": datetime.now()
        }
        
        # Remove await - use regular insert_one
        db.conversations.insert_one(message_data)
        return True
    
    def _get_user_context(self, user_id):
        """Lấy context hiện tại của người dùng (synchronous version)"""
        user_data = db.users.find_one({"user_id": user_id})
        if user_data and "context" in user_data:
            return user_data["context"]
        return None

    def _update_user_context(self, user_id, context_update):
        """Cập nhật context của người dùng"""
        result = db.users.update_one(
            {"user_id": user_id},
            {"$set": context_update},
            upsert=True
        )
        return result

# Khởi tạo message handler
message_handler = MessageHandler()