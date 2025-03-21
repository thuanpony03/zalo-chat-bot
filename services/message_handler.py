from datetime import datetime, timedelta
import asyncio
import json
import logging
import traceback
import redis
import re
import time
from .tour_processor import TourPriceProcessor
from services.zalo_api import ZaloAPI
from services.ai_processor import ai_processor  # Thêm import ai_processor
from services.admin_commands import admin_handler  # Thêm import admin_commands

# Initialize Redis client
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MessageHandler:
    def __init__(self):
        self.tour_processor = TourPriceProcessor()
        self.zalo_api = ZaloAPI()
        self.pending_messages = {}  # {user_id: {'messages': [], 'last_time': timestamp}}
        self.waiting_time = 5  # Thời gian chờ 5 giây để gộp tin nhắn

    async def process_message(self, message, sender_id):
        """Thêm tin nhắn vào hàng đợi và lên lịch xử lý sau thời gian chờ."""
        try:
            # Kiểm tra nếu là lệnh admin
            text = message.get('text', '')
            if text.startswith('/'):
                success, response = admin_handler.process_command(text, sender_id)
                if response:  # Nếu có phản hồi từ admin command
                    return [response]
            
            # Kiểm tra nếu bot đang bị tạm dừng cho user này
            if admin_handler.is_bot_paused_for_user(sender_id):
                logger.info(f"Bot đang tạm dừng cho user {sender_id}, bỏ qua tin nhắn")
                return None  # Không trả lời nếu bot đang bị tạm dừng
            
            # Xử lý bình thường nếu bot không bị tạm dừng
            current_time = time.time()
            if sender_id not in self.pending_messages:
                self.pending_messages[sender_id] = {'messages': [], 'last_time': current_time}
            
            self.pending_messages[sender_id]['messages'].append(message)
            self.pending_messages[sender_id]['last_time'] = current_time
            
            # Lên lịch xử lý nếu chưa có
            if not hasattr(self, f"task_{sender_id}"):
                task = asyncio.create_task(self._schedule_processing(sender_id))
                setattr(self, f"task_{sender_id}", task)
            
            return None  # Không trả về ngay, chờ xử lý sau

        except Exception as e:
            logger.error(f"Lỗi khi xử lý tin nhắn: {str(e)}")
            traceback.print_exc()
            return ["Xin lỗi, đã xảy ra lỗi. Vui lòng thử lại sau."]

    async def _schedule_processing(self, user_id):
        """Lên lịch xử lý tin nhắn sau thời gian chờ."""
        await asyncio.sleep(self.waiting_time)
        
        # Kiểm tra lại xem bot có đang bị tạm dừng không sau khi đã chờ
        if admin_handler.is_bot_paused_for_user(user_id):
            logger.info(f"Bot đang tạm dừng cho user {user_id}, bỏ qua xử lý tin nhắn")
            if hasattr(self, f"task_{user_id}"):
                delattr(self, f"task_{user_id}")  # Xóa task sau khi kiểm tra
            return
            
        current_time = time.time()
        if user_id in self.pending_messages and (current_time - self.pending_messages[user_id]['last_time']) >= self.waiting_time:
            await self._process_pending_messages(user_id)
            if hasattr(self, f"task_{user_id}"):
                delattr(self, f"task_{user_id}")  # Xóa task sau khi xử lý

    async def _process_pending_messages(self, user_id):
        """Xử lý tất cả tin nhắn trong hàng đợi."""
        try:
            if user_id not in self.pending_messages:
                return
            
            messages = self.pending_messages[user_id]['messages']
            del self.pending_messages[user_id]  # Xóa sau khi lấy
            
            if not messages:
                return
            
            # Gộp tất cả tin nhắn thành một chuỗi
            combined_text = " ".join([msg.get('text', '') for msg in messages])
            logger.info(f"Processing combined text for user {user_id}: {combined_text}")
            
            # Xử lý các yêu cầu đặc biệt về lịch trình chi tiết hoặc nâng cấp dịch vụ
            detailed_itinerary_keywords = ["lịch trình chi tiết", "chi tiết từng ngày", "lịch trình cụ thể", "có", "cần", "muốn", "đồng ý", "ok", "được"]
            upgrade_keywords = ["nâng cấp", "khách sạn", "vé máy bay", "phòng", "5 sao", "4 sao"]
            
            context = json.loads(redis_client.get(f"context:{user_id}") or '{}')
            
            # Phát hiện intent
            intent = await self._detect_intent(combined_text, user_id)
            
            # Xử lý dựa trên intent
            if intent == "visa":
                responses = await self._handle_visa_query(combined_text, user_id)
            else:  # intent == "tour" hoặc khác
                if any(keyword in combined_text.lower() for keyword in detailed_itinerary_keywords) and context.get("country"):
                    # Xử lý yêu cầu lịch trình chi tiết
                    response = (
                        f"Dạ, với tour {context.get('country', '')} {context.get('days', '')} ngày, em có thể chia sẻ lịch trình chi tiết từng ngày đã được chuyên gia du lịch thiết kế. "
                        f"Anh/chị vui lòng để lại tên và số điện thoại hoặc gọi hotline 1900 636563, nhân viên tư vấn sẽ gửi chi tiết lịch trình và tư vấn cụ thể theo nhu cầu của gia đình mình ạ!"
                    )
                    responses = [response]
                elif any(keyword in combined_text.lower() for keyword in upgrade_keywords):
                    # Xử lý yêu cầu nâng cấp dịch vụ
                    response = (
                        f"Dạ, để nâng cấp dịch vụ cho tour, chúng tôi có nhiều lựa chọn phù hợp với nhu cầu của gia đình anh/chị. "
                        f"Anh/chị vui lòng để lại tên và số điện thoại hoặc gọi hotline 1900 636563, nhân viên tư vấn sẽ liên hệ ngay với các gói dịch vụ nâng cấp tốt nhất ạ!"
                    )
                    responses = [response]
                else:
                    responses = await self._handle_tour_query(combined_text, user_id)
            
            # Gửi phản hồi
            await self._send_response(user_id, responses if responses else ["Dạ, em chưa hiểu rõ yêu cầu. Anh/chị vui lòng cung cấp thêm thông tin nhé!"])
            
        except Exception as e:
            logger.error(f"Lỗi khi xử lý hàng đợi tin nhắn: {e}")
            await self._send_response(user_id, ["Xin lỗi, đã xảy ra lỗi. Vui lòng thử lại sau."])

    async def _detect_intent(self, text, user_id):
        """Phát hiện ý định của người dùng sử dụng logic đơn giản."""
        text_lower = text.lower()
        
        # Lấy context hiện tại từ Redis
        context = json.loads(redis_client.get(f"context:{user_id}") or '{}')
        previous_intent = context.get("service_type")
        
        # Từ khóa liên quan đến visa
        visa_keywords = [
            "visa", "thị thực", "hộ chiếu", "lãnh sự", "đại sứ quán", 
            "xin visa", "làm visa", "passport", "hồ sơ", "giấy tờ", 
            "xuất cảnh", "nhập cảnh", "quá cảnh", "công chứng", "dịch thuật"
        ]
        
        # Từ khóa liên quan đến tour
        tour_keywords = [
            "du lịch", "tour", "đi chơi", "tham quan", "attraction", 
            "nghỉ dưỡng", "resort", "lịch trình", "chương trình tour", 
            "khách sạn", "vé máy bay", "địa điểm"
        ]

        # Nếu tin nhắn chứa reset, giữ intent trước đó
        if "reset" in text_lower:
            return previous_intent or "tour"  # Default to tour
            
        # Đếm số từ khóa visa và tour
        visa_score = sum(1 for keyword in visa_keywords if keyword in text_lower)
        tour_score = sum(1 for keyword in tour_keywords if keyword in text_lower)
        
        # Quyết định dựa trên điểm số
        if visa_score > tour_score:
            intent = "visa"
        elif tour_score > visa_score:
            intent = "tour"
        else:
            # Nếu cả hai bằng nhau hoặc bằng 0, giữ intent trước đó
            intent = previous_intent or "tour"  # Default to tour
            
        # Cập nhật intent vào context
        context["service_type"] = intent
        redis_client.set(f"context:{user_id}", json.dumps(context))
        
        return intent

    async def _handle_tour_query(self, text, user_id):
        """Xử lý yêu cầu tour bằng TourPriceProcessor."""
        try:
            result = await self.tour_processor.process_tour_query(user_id, text)
            
            # If result is a tuple (messages, context), extract just the messages
            if isinstance(result, tuple) and len(result) >= 1:
                messages = result[0]
            else:
                messages = result
                
            # Now ensure messages is a list
            if not isinstance(messages, list):
                messages = [messages]
                
            return messages
        except Exception as e:
            logger.error(f"Lỗi khi xử lý tour query: {e}")
            traceback.print_exc()
            return ["Dạ, em gặp lỗi khi xử lý yêu cầu tour. Anh/chị thử lại nhé!"]

    async def _handle_visa_query(self, text, user_id):
        """Xử lý yêu cầu visa bằng AIProcessor."""
        try:
            # Lấy context hiện tại từ Redis
            context = json.loads(redis_client.get(f"context:{user_id}") or '{}')
            
            # Thêm user_id vào context
            context['user_id'] = user_id
            
            # Lấy lịch sử hội thoại
            previous_messages = json.loads(redis_client.get(f"history:{user_id}") or '[]')
            if previous_messages:
                formatted_messages = []
                for msg in previous_messages:
                    if msg.startswith("User:"):
                        formatted_messages.append({"sender": "user", "message": msg[5:].strip()})
                    elif msg.startswith("Bot:"):
                        formatted_messages.append({"sender": "bot", "message": msg[4:].strip()})
                context['previous_messages'] = formatted_messages
            
            # Gọi AI Processor để xử lý yêu cầu visa
            response, new_context = await ai_processor.process_visa_query(text, context)
            
            # Cập nhật context mới vào Redis
            redis_client.set(f"context:{user_id}", json.dumps(new_context))
            
            # Lưu vào lịch sử
            history = json.loads(redis_client.get(f"history:{user_id}") or '[]')
            history.append(f"User: {text}")
            history.append(f"Bot: {response}")
            redis_client.set(f"history:{user_id}", json.dumps(history[-10:]))  # Giữ 10 tin nhắn gần nhất
            
            return [response]
        except Exception as e:
            logger.error(f"Lỗi khi xử lý visa query: {e}")
            traceback.print_exc()
            return ["Dạ, em gặp lỗi khi xử lý yêu cầu visa. Anh/chị vui lòng thử lại hoặc gọi hotline 1900 636563 để được hỗ trợ trực tiếp."]

    async def _send_response(self, user_id, responses):
        """Gửi phản hồi qua Zalo API bất đồng bộ."""
        if not isinstance(responses, list):
            responses = [responses]
        
        for msg in responses:
            if msg and msg.strip():
                try:
                    result = self.zalo_api.send_text_message(user_id, msg.strip())
                    logger.info(f"Sent response to {user_id}: {msg.strip()} - Result: {result}")
                    if result.get("error", 0) != 0:
                        logger.error(f"Failed to send message '{msg.strip()}': {result}")
                    await asyncio.sleep(1)  # Đợi 1 giây giữa các tin nhắn bất đồng bộ
                except Exception as e:
                    logger.error(f"Error sending message '{msg.strip()}': {e}")

message_handler = MessageHandler()

