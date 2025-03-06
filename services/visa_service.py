# Service for visa_service
# Created: 2025-03-04 23:44:55
# Author: thuanpony03

from bson import ObjectId
from services.database import db
from services.visa_repository import visa_repository
from nltk import word_tokenize
import re

class VisaService:
    def __init__(self):
        self.repository = visa_repository
        self.common_countries = {
            "nhật bản": ["nhật", "japan", "nhat", "nhat ban"],
            "hàn quốc": ["hàn", "korea", "han", "han quoc"],
            "mỹ": ["my", "usa", "america", "united states"],
            "trung quốc": ["trung quoc", "china"],
            "úc": ["australia", "uc", "au"],
            "canada": ["canada"],
            "anh": ["anh", "england", "uk"],
            "pháp": ["phap", "france"],
            "đức": ["duc", "germany"],
            "ý": ["y", "italy"],
            "tây ban nha": ["tay ban nha", "spain"],
            "hà lan": ["ha lan", "netherlands"],
            "singapore": ["singapore", "sing"]
        }
        
        self.visa_types = {
            "du lịch": ["du lich", "tourist", "travel"],
            "thương mại": ["thuong mai", "business"],
            "công tác": ["cong tac", "business"],
            "du học": ["du hoc", "student", "study"],
            "kết hôn": ["ket hon", "marriage"],
            "định cư": ["dinh cu", "settlement", "immigrant"],
            "nhiều lần": ["nhieu lan", "multiple", "multiple entry"],
            "khẩn": ["khan", "urgent", "express"]
        }
    
    def extract_visa_query_info(self, message):
        """Trích xuất thông tin quốc gia và loại visa từ câu hỏi"""
        message = message.lower()
        
        # Tìm quốc gia
        extracted_country = None
        for country, aliases in self.common_countries.items():
            if country in message or any(alias in message for alias in aliases):
                extracted_country = country
                break
        
        # Tìm loại visa
        extracted_type = None
        for visa_type, aliases in self.visa_types.items():
            if visa_type in message or any(alias in message for alias in aliases):
                extracted_type = visa_type
                break
                
        # Mặc định là du lịch nếu không tìm thấy loại visa
        if not extracted_type and extracted_country:
            extracted_type = "du lịch"
            
        return {
            "country": extracted_country,
            "visa_type": extracted_type
        }
    
    def get_visa_info(self, message):
        """Lấy thông tin visa dựa trên câu hỏi"""
        query_info = self.extract_visa_query_info(message)
        
        if not query_info["country"]:
            return {
                "success": False,
                "message": "Vui lòng nêu rõ quốc gia cần xin visa."
            }
            
        visas = self.repository.find_by_country_and_type(
            query_info["country"], 
            query_info["visa_type"]
        )
        
        if not visas:
            return {
                "success": False,
                "message": f"Không tìm thấy thông tin visa {query_info['visa_type'] or ''} cho {query_info['country']}."
            }
            
        if len(visas) == 1:
            return {
                "success": True,
                "data": visas[0],
                "type": "single"
            }
        else:
            return {
                "success": True,
                "data": visas,
                "type": "multiple"
            }
    
    def format_visa_response(self, visa_info, detailed=True):
        """Định dạng phản hồi thông tin visa"""
        if not visa_info or not visa_info["success"]:
            return visa_info["message"]
            
        if visa_info["type"] == "multiple":
            # Hiển thị danh sách visa
            visas = visa_info["data"]
            response = f"🛂 CÁC LOẠI VISA {visas[0]['country'].upper()}:\n\n"
            
            for i, visa in enumerate(visas, 1):
                response += f"{i}. Visa {visa['visa_type']}\n"
                response += f"   ⏱️ Thời gian xử lý: {visa['processing_time']}\n"
                response += f"   💰 Phí: {'{:,.0f}'.format(visa['price']).replace(',', '.')} VNĐ\n\n"
                
            response += "Bạn muốn tìm hiểu chi tiết về loại visa nào? (Nhập số thứ tự 1, 2, 3...)"
            return response
            
        else:
            # Hiển thị chi tiết 1 visa
            visa = visa_info["data"]
            response = f"🛂 VISA {visa['visa_type'].upper()} {visa['country'].upper()}\n\n"
            response += f"⏱️ Thời gian xử lý: {visa['processing_time']}\n"
            response += f"💰 Phí: {'{:,.0f}'.format(visa['price']).replace(',', '.')} VNĐ\n"
            response += f"⏳ Thời hạn: {visa['validity']}\n\n"
            
            if detailed and "requirements" in visa:
                # Hiển thị chi tiết yêu cầu hồ sơ
                response += "📋 YÊU CẦU HỒ SƠ:\n"
                
                # Nếu có cấu trúc phân loại
                if isinstance(visa["requirements"], dict):
                    if "personal_docs" in visa["requirements"]:
                        response += "\n▶️ Hồ sơ cá nhân:\n"
                        for i, req in enumerate(visa["requirements"]["personal_docs"], 1):
                            response += f"{i}. {req}\n"
                            
                    if "financial_docs" in visa["requirements"]:
                        response += "\n▶️ Chứng minh tài chính:\n"
                        for i, req in enumerate(visa["requirements"]["financial_docs"], 1):
                            response += f"{i}. {req}\n"
                    
                    if "travel_docs" in visa["requirements"]:
                        response += "\n▶️ Tài liệu du lịch:\n"
                        for i, req in enumerate(visa["requirements"]["travel_docs"], 1):
                            response += f"{i}. {req}\n"
                    
                    if "employment_docs" in visa["requirements"]:
                        response += "\n▶️ Hồ sơ công việc:\n"
                        for i, req in enumerate(visa["requirements"]["employment_docs"], 1):
                            response += f"{i}. {req}\n"
                else:
                    # Nếu là list thông thường
                    for i, req in enumerate(visa["requirements"], 1):
                        response += f"{i}. {req}\n"
            
            if "notes" in visa and visa["notes"]:
                response += f"\n📝 LƯU Ý: {visa['notes']}\n"
                
            if "success_rate" in visa and visa["success_rate"]:
                response += f"\n✅ Tỷ lệ thành công: {visa['success_rate']}\n"
                
            response += "\n📞 Bạn có thể liên hệ hotline 1900 636563 để được tư vấn chi tiết!"
            
            return response
    
    def get_all_visas(self):
        """Lấy tất cả thông tin visa"""
        return list(self.repository.collection.find())

# Khởi tạo service
visa_service = VisaService()