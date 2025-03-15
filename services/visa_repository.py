from services.database import db
from bson import ObjectId
import re

class VisaRepository:
    def __init__(self):
        self.collection = db.get_collection("visas")  # Fixed: use get_collection instead of direct attribute access
        self.cache = {}  # Simple in-memory cache
    
    def find_by_country_and_type(self, country, visa_type=None):
        """Tìm thông tin visa theo quốc gia và loại visa với khả năng tìm kiếm nâng cao"""
        # Tạo cache key
        cache_key = f"{country.lower()}:{visa_type.lower() if visa_type else 'all'}"
        
        # Kiểm tra cache
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        # Xây dựng query
        query = {}
        
        # Tìm kiếm nâng cao với các alias và kết hợp regex
        country_pattern = self._build_search_pattern(country)
        query["$or"] = [
            {"country": {"$regex": country_pattern, "$options": "i"}},
            {"country_aliases": {"$regex": country_pattern, "$options": "i"}}
        ]
        
        # Nếu có loại visa cụ thể
        if visa_type:
            type_pattern = self._build_search_pattern(visa_type)
            query["$and"] = [{
                "$or": [
                    {"visa_type": {"$regex": type_pattern, "$options": "i"}},
                    {"type_aliases": {"$regex": type_pattern, "$options": "i"}}
                ]
            }]
        
        # Thực hiện truy vấn
        results = list(self.collection.find(query))
        
        # Lưu vào cache
        self.cache[cache_key] = results
        
        return results
    
    def find_by_id(self, visa_id):
        """Tìm visa theo ID"""
        try:
            if isinstance(visa_id, str):
                visa_id = ObjectId(visa_id)
            return self.collection.find_one({"_id": visa_id})
        except:
            return None
    
    def get_all_visa_types_for_country(self, country):
        """Lấy tất cả loại visa cho một quốc gia"""
        country_pattern = self._build_search_pattern(country)
        query = {
            "$or": [
                {"country": {"$regex": country_pattern, "$options": "i"}},
                {"country_aliases": {"$regex": country_pattern, "$options": "i"}}
            ]
        }
        
        results = list(self.collection.find(query, {"visa_type": 1, "price": 1, "processing_time": 1}))
        return results
    
    def _build_search_pattern(self, search_term):
        """Xây dựng pattern tìm kiếm thông minh hơn"""
        # Xử lý từ khóa tìm kiếm, bỏ dấu, chuyển thành pattern linh hoạt
        search_term = search_term.lower()
        # Xử lý các trường hợp đặc biệt (để tìm kiếm chính xác hơn)
        if re.search(r'mỹ|my|usa|america', search_term):
            return 'mỹ|my|usa|america'
        elif re.search(r'nhật|nhat|japan', search_term):
            return 'nhật|nhat|japan'
        elif re.search(r'hàn|han|korea', search_term):
            return 'hàn|han|korea'
        elif re.search(r'châu âu|chau au|eu|europe|schengen', search_term):
            return 'châu âu|chau au|eu|europe|schengen'
        else:
            # Mặc định trả về từ khóa gốc
            return search_term
    
    def clear_cache(self):
        """Xóa cache"""
        self.cache = {}

# Khởi tạo repository
visa_repository = VisaRepository()