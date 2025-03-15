import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Các cấu hình hiện tại
    
    # Cập nhật địa chỉ MongoDB nếu bạn đang sử dụng container
    MONGODB_URI = "mongodb://admin:password@localhost:27017"
    MONGODB_DB = "zalo_chatbot"
    
    # Các cấu hình khác giữ nguyên
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    COMPANY_NAME = "Passport Lounge"
    HOTLINE = "1900 636563"

if not Config.GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is required in .env file")