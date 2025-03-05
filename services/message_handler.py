class MessageHandler:
    async def process_message(self, user_id, message):
        """Process incoming messages from users"""
        # Simple response for testing
        return f"Đã nhận được tin nhắn: {message}"

# Tạo instance để sử dụng trong app.py
message_handler = MessageHandler()