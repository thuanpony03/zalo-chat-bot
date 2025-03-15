from datetime import datetime, timedelta
import asyncio
import logging
from .ai_processor import ai_processor  # Import từ file ai_processor

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MessageHandler:
    def __init__(self):
        from services.database import db
        self.db = db

    async def process_message(self, user_id, message):
        """Xử lý tin nhắn từ người dùng"""
        try:
            context = self._get_user_context(user_id) or {}
            self._save_message_to_history(user_id, "user", message)
            context['previous_messages'] = self._get_recent_messages(user_id, limit=5)
            
            if message.lower() in ["reset", "khởi động lại", "bắt đầu lại"]:
                self._update_user_context(user_id, {})
                return "Đã reset trạng thái hội thoại. Bạn có thể bắt đầu lại với một câu hỏi mới."
            
            response, new_context = await ai_processor.process_visa_query(message, context)
            self._save_message_to_history(user_id, "bot", response)
            self._update_user_context(user_id, new_context)
            return response
            
        except Exception as e:
            logger.error(f"Lỗi khi xử lý tin nhắn: {e}", exc_info=True)
            return "Xin lỗi, đã xảy ra lỗi. Vui lòng liên hệ hotline 1900 636563 để được hỗ trợ."

    def _get_user_context(self, user_id):
        """Lấy ngữ cảnh hiện tại của người dùng"""
        try:
            users_collection = self.db.get_collection("users")
            user_data = users_collection.find_one({"user_id": user_id})
            return user_data.get("context") if user_data and "context" in user_data else {}
        except Exception as e:
            logger.error(f"Lỗi khi lấy context: {e}")
            return {}

    def _update_user_context(self, user_id, context):
        """Cập nhật ngữ cảnh người dùng"""
        try:
            users_collection = self.db.get_collection("users")
            if "last_updated" in context and (datetime.now() - context["last_updated"]) > timedelta(hours=24):
                context = {}
            context["last_updated"] = datetime.now()
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"context": context}},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật context: {e}")
            return False

    def _save_message_to_history(self, user_id, sender, message):
        """Lưu tin nhắn vào lịch sử"""
        try:
            messages_collection = self.db.get_collection("messages")
            messages_collection.insert_one({
                "user_id": user_id,
                "sender": sender,
                "message": message,
                "timestamp": datetime.now()
            })
            return True
        except Exception as e:
            logger.error(f"Lỗi khi lưu tin nhắn: {e}")
            return False

    def _get_recent_messages(self, user_id, limit=5):
        """Lấy tin nhắn gần đây"""
        try:
            messages_collection = self.db.get_collection("messages")
            messages = list(messages_collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit))
            return [{"sender": m["sender"], "message": m["message"]} for m in reversed(messages)]
        except Exception as e:
            logger.error(f"Lỗi khi lấy tin nhắn: {e}")
            return []

message_handler = MessageHandler()
