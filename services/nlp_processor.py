# Service for nlp_processor
# Created: 2025-03-04 23:44:55
# Author: thuanpony03

import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
import re
import os
import pickle
import numpy as np
from services.database import db

# Tải các resources cần thiết
nltk.download('punkt')
nltk.download('stopwords')

class NLPProcessor:
    def __init__(self):
        self.stemmer = PorterStemmer()
        
        # Fix: Use only English stopwords since Vietnamese isn't included in NLTK
        self.stop_words = set(stopwords.words('english'))
        
        # Add some common Vietnamese stopwords manually
        vietnamese_stopwords = {
            "của", "và", "các", "có", "được", "cho", "là", "vào", "trong", 
            "những", "với", "để", "này", "khi", "bạn", "từ", "một", "không", 
            "còn", "về", "như", "tôi", "đã", "sẽ", "tại", "thì", "cũng"
        }
        self.stop_words.update(vietnamese_stopwords)
        
        # Dictionary lưu trữ các patterns và intents
        self.patterns = {
            'TOUR_SEARCH': [
                r'tìm tour', r'tour du lịch', r'đi du lịch', r'gói du lịch',
                r'tour.*nước ngoài', r'tour châu', r'tour.*ưu đãi'
            ],
            'VISA_INFO': [
                r'visa', r'làm visa', r'thủ tục visa', r'xin visa', 
                r'hồ sơ visa', r'phí visa', r'visa.*nước'
            ],
            'PASSPORT_INFO': [
                r'hộ chiếu', r'passport', r'làm hộ chiếu', r'gia hạn.*hộ chiếu',
                r'thủ tục.*hộ chiếu', r'passport.*hết hạn'
            ],
            'FLIGHT_INFO': [
                r'vé máy bay', r'chuyến bay', r'đặt vé', r'đặt chỗ bay',
                r'bay.*nước ngoài', r'giá vé.*bay'
            ],
            'WEATHER_INFO': [
                r'thời tiết', r'dự báo', r'mưa', r'nắng', r'nhiệt độ'
            ],
            'BOOKING_ACTION': [
                r'đặt tour', r'book', r'đặt lịch', r'đăng ký tour',
                r'thanh toán', r'đặt chỗ'
            ],
            'BOOKING_STATUS': [
                r'kiểm tra.*đặt', r'tình trạng', r'đã đặt.*chưa', 
                r'xác nhận.*đặt', r'hủy.*đặt'
            ],
            'FAQ': [
                r'câu hỏi', r'thắc mắc', r'hỏi', r'giải đáp', 
                r'tư vấn', r'làm sao để'
            ],
            'GREETING': [
                r'xin chào', r'hello', r'hi', r'chào', r'hey'
            ]
        }
        
    def preprocess_text(self, text):
        """Tiền xử lý văn bản"""
        # Chuyển text về chữ thường
        text = text.lower()
        
        # Loại bỏ các ký tự đặc biệt
        text = re.sub(r'[^\w\s]', '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Loại bỏ stopwords và stemming
        tokens = [self.stemmer.stem(word) for word in tokens if word not in self.stop_words]
        
        return tokens
        
    def extract_entities(self, text):
        """Trích xuất các thực thể từ văn bản"""
        entities = {
            'locations': [],
            'dates': [],
            'people': None,
            'price': None
        }
        
        # Trích xuất địa điểm
        # Giả sử chúng ta có danh sách các địa điểm trong CSDL
        locations = list(db.locations.find({}, {"name": 1}))
        location_names = [location["name"].lower() for location in locations]
        
        for location_name in location_names:
            if location_name in text.lower():
                entities['locations'].append(location_name)
                
        # Trích xuất ngày tháng
        date_regex = r'\d{1,2}\/\d{1,2}(\/\d{2,4})?'
        date_matches = re.findall(date_regex, text)
        
        if date_matches:
            entities['dates'] = date_matches
            
        # Trích xuất số người
        people_regex = r'(\d+)\s*(người|khách|du khách|người lớn|trẻ em)'
        people_match = re.search(people_regex, text, re.IGNORECASE)
        
        if people_match:
            entities['people'] = int(people_match.group(1))
            
        # Trích xuất giá cả
        price_regex = r'(dưới|trên|khoảng)?\s*(\d+)\s*(triệu|nghìn|k|tr)'
        price_match = re.search(price_regex, text, re.IGNORECASE)
        
        if price_match:
            price = int(price_match.group(2))
            unit = price_match.group(3).lower()
            
            if unit == 'tr' or unit == 'triệu':
                price *= 1000000
            elif unit == 'k' or unit == 'nghìn':
                price *= 1000
                
            entities['price'] = {
                'value': price,
                'condition': price_match.group(1) or 'khoảng'
            }
            
        return entities
        
    def classify_intent(self, text):
        """Phân loại ý định từ văn bản"""
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, text.lower()):
                    return intent
        
        return "UNKNOWN"
    
    def analyze_message(self, message):
        """Phân tích tin nhắn để xác định ý định và thực thể"""
        # Phân loại ý định
        intent = self.classify_intent(message)
        
        # Trích xuất thực thể
        entities = self.extract_entities(message)
        
        return {
            "intent": intent,
            "entities": entities,
            "original_message": message
        }