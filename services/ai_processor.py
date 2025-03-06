import os
import google.generativeai as genai
from dotenv import load_dotenv
from services.visa_service import visa_service

load_dotenv()

class AIProcessor:
    def __init__(self):
        # Cấu hình Gemini API
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("CẢNH BÁO: Không tìm thấy GEMINI_API_KEY trong biến môi trường")
        genai.configure(api_key=api_key)
        
        # Thiết lập model Gemini
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Định nghĩa system prompt
        self.system_prompt = """
        Bạn là trợ lý ảo của Passport Lounge, một công ty du lịch Việt Nam. 
        
        CÁCH XỬ LÝ CÂU HỎI VỀ VISA:
        - Khi nhận được câu hỏi về visa, luôn tham khảo dữ liệu chính xác được cung cấp trong phần VISA_DATA
        - Dựa vào thông tin visa được cung cấp, trả lời chi tiết và đầy đủ
        - Không tự tạo thông tin về giá cả, thủ tục hay yêu cầu - chỉ sử dụng dữ liệu được cung cấp
        
        Đặc điểm phản hồi:
        - Thân thiện và chuyên nghiệp
        - Trả lời bằng tiếng Việt, ngắn gọn nhưng đầy đủ thông tin
        - Sử dụng emoji phù hợp (😊, 🌎, ✈️, 🏨, etc.)
        - Khuyến khích khách hàng liên hệ trực tiếp để được tư vấn chi tiết
        - Hotline: 1900 636563
        """
    
    async def generate_response(self, user_message, context=None):
        """Tạo phản hồi thông minh từ Gemini AI"""
        try:
            # Kiểm tra nếu câu hỏi về visa
            if self._is_visa_query(user_message):
                # Lấy thông tin visa từ database
                visa_info = visa_service.get_visa_info(user_message)
                
                # Nếu có thông tin visa, tạo response từ database
                if visa_info["success"]:
                    visa_response = visa_service.format_visa_response(visa_info)
                    return visa_response
                else:
                    # Không tìm thấy thông tin visa, để AI trả lời dựa trên context
                    additional_context = f"Không tìm thấy thông tin visa chính xác cho câu hỏi: {user_message}"
            
            # Xây dựng prompt với thông tin từ system prompt
            prompt = self.system_prompt + "\n\n" + user_message
            
            # Thêm context nếu có
            if context:
                history_text = ""
                if "previous_messages" in context and context["previous_messages"]:
                    history_text = "Lịch sử trò chuyện gần đây:\n"
                    for msg in context["previous_messages"][-3:]:
                        sender = "Bot" if msg.get('sender') == "bot" else "Người dùng"
                        history_text += f"{sender}: {msg.get('message', '')}\n"
                
                # Thêm context vào cuối prompt
                if history_text:
                    prompt = prompt + "\n\nĐây là lịch sử trò chuyện gần đây:\n" + history_text
            
            # Gửi prompt tới Gemini
            response = self.model.generate_content(prompt)
            
            # Lấy text từ response
            if hasattr(response, 'text'):
                return response.text
            else:
                return "Xin lỗi, tôi không thể trả lời câu hỏi của bạn lúc này."
            
        except Exception as e:
            print(f"Error in AI response generation: {e}")
            return self._get_fallback_response()
    
    def _is_visa_query(self, message):
        """Kiểm tra xem tin nhắn có phải là câu hỏi về visa không"""
        message = message.lower()
        visa_keywords = ["visa", "thị thực", "xin visa", "làm visa", "hồ sơ visa", "thủ tục visa"]
        
        return any(keyword in message for keyword in visa_keywords)
    
    def _get_fallback_response(self):
        """Trả về câu trả lời dự phòng khi AI gặp lỗi"""
        import random
        fallbacks = [
            "Xin lỗi, tôi đang gặp vấn đề kết nối. Bạn có thể hỏi lại sau được không? 😊",
            "Tôi không thể trả lời ngay lúc này. Bạn có thể liên hệ hotline 1900 636563 để được hỗ trợ nhanh nhất.",
            "Hệ thống đang bận, vui lòng thử lại sau nhé! Hoặc bạn có thể liên hệ trực tiếp với nhân viên tư vấn của chúng tôi.",
            "Xin lỗi vì sự bất tiện này. Tôi đang gặp khó khăn trong việc xử lý yêu cầu. Bạn có thể thử lại sau ít phút?",
            "Rất tiếc, tôi không thể xử lý yêu cầu của bạn lúc này. Hãy liên hệ hotline 1900 636563 để được hỗ trợ ngay!"
        ]
        return random.choice(fallbacks)

    def update_user_preferences(self, user_id, message, entities):
        """Cập nhật thông tin sở thích của người dùng"""
        from services.database import db
        
        user_data = db.users.find_one({"user_id": user_id}) or {"user_id": user_id}
        preferences = user_data.get("preferences", {})
        
        # Phân tích và lưu sở thích
        if entities and entities.get("locations"):
            if "preferred_destinations" not in preferences:
                preferences["preferred_destinations"] = []
            for location in entities["locations"]:
                if location not in preferences["preferred_destinations"]:
                    preferences["preferred_destinations"].append(location)
        
        # Phát hiện sở thích về ngân sách
        message_lower = message.lower()
        if "giá rẻ" in message_lower or "tiết kiệm" in message_lower:
            preferences["budget"] = "low"
        elif "sang trọng" in message_lower or "cao cấp" in message_lower:
            preferences["budget"] = "high"
        
        # Cập nhật dữ liệu người dùng
        db.users.update_one(
            {"user_id": user_id},
            {"$set": {"preferences": preferences}},
            upsert=True
        )
        return preferences

# Khởi tạo AI processor
ai_processor = AIProcessor()