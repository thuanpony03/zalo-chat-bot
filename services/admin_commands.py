import logging
import redis
import json
import time
from datetime import datetime, timedelta

# Redis setup
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

logger = logging.getLogger(__name__)

class AdminCommandHandler:
    """Xử lý các lệnh admin để kiểm soát bot"""
    
    # Danh sách admin có thể là rỗng, cho phép bất kỳ ai cũng có thể dùng lệnh trong chat của họ
    ADMIN_USERS = []  
    
    @staticmethod
    def process_command(text, sender_id):
        """Xử lý lệnh admin trong cuộc trò chuyện hiện tại"""
        # Lệnh tạm dừng bot
        if text.startswith("/stop"):
            parts = text.split()
            minutes = 30  # Thời gian mặc định nếu không cung cấp
            
            if len(parts) >= 2:
                try:
                    minutes = int(parts[1])
                except ValueError:
                    return False, "Thời gian phải là số (phút). Ví dụ: /stop 30"
                
            return AdminCommandHandler.stop_bot_for_user(sender_id, minutes)
            
        # Lệnh khôi phục bot
        elif text.startswith("/resume"):
            return AdminCommandHandler.resume_bot_for_user(sender_id)
            
        # Lệnh kiểm tra trạng thái
        elif text.startswith("/status"):
            return AdminCommandHandler.check_bot_status(sender_id)
            
        return None, None  # Không phải lệnh admin
    
    @staticmethod
    def stop_bot_for_user(user_id, minutes):
        """Tạm dừng bot cho một user trong khoảng thời gian xác định"""
        try:
            expiry_time = datetime.now() + timedelta(minutes=minutes)
            data = {
                "paused_at": datetime.now().timestamp(),
                "resume_at": expiry_time.timestamp(),
                "paused_by": "admin"
            }
            
            # Lưu trạng thái tạm dừng vào Redis với thời gian hết hạn
            redis_client.setex(
                f"botpause:{user_id}", 
                int(minutes * 60),  # Convert to seconds for Redis expiry
                json.dumps(data)
            )
            
            end_time = expiry_time.strftime("%H:%M:%S, %d/%m/%Y")
            
            logger.info(f"Bot đã tạm dừng cho user {user_id} trong {minutes} phút, đến {end_time}")
            return True, f"Đã tạm dừng bot trong {minutes} phút, tư vấn viên có thể trực tiếp tư vấn khách hàng. Bot sẽ tự động hoạt động lại lúc {end_time}"
        except Exception as e:
            logger.error(f"Lỗi khi tạm dừng bot: {e}")
            return False, f"Lỗi khi tạm dừng bot: {str(e)}"
    
    @staticmethod
    def resume_bot_for_user(user_id):
        """Khôi phục bot cho một user trước thời gian hết hạn"""
        try:
            pause_key = f"botpause:{user_id}"
            if not redis_client.exists(pause_key):
                return False, f"Bot không bị tạm dừng cho cuộc hội thoại này"
                
            # Xóa key tạm dừng
            redis_client.delete(pause_key)
            
            logger.info(f"Bot đã được khôi phục cho user {user_id}")
            return True, f"Bot đã được khôi phục và sẵn sàng phản hồi lại"
        except Exception as e:
            logger.error(f"Lỗi khi khôi phục bot: {e}")
            return False, f"Lỗi khi khôi phục bot: {str(e)}"
    
    @staticmethod
    def check_bot_status(user_id):
        """Kiểm tra trạng thái bot cho một user"""
        try:
            pause_key = f"botpause:{user_id}"
            if not redis_client.exists(pause_key):
                return True, f"Bot đang hoạt động bình thường trong cuộc hội thoại này"
                
            pause_data = json.loads(redis_client.get(pause_key))
            resume_time = datetime.fromtimestamp(pause_data["resume_at"])
            remaining = (resume_time - datetime.now()).total_seconds() / 60
            
            return True, f"Bot đang tạm dừng, còn {remaining:.1f} phút nữa sẽ tự động hoạt động lại"
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra trạng thái bot: {e}")
            return False, f"Lỗi khi kiểm tra trạng thái bot: {str(e)}"
    
    @staticmethod
    def is_bot_paused_for_user(user_id):
        """Kiểm tra xem bot có đang bị tạm dừng cho user không"""
        try:
            pause_key = f"botpause:{user_id}"
            return redis_client.exists(pause_key)
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra trạng thái tạm dừng: {e}")
            return False

admin_handler = AdminCommandHandler()