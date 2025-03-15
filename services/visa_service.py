# Service for visa_service
# Created: 2025-03-04 23:44:55
# Author: thuanpony03

from bson import ObjectId
from services.database import db
from services.visa_repository import visa_repository
from nltk import word_tokenize
import re
from fuzzywuzzy import process, fuzz
from datetime import datetime

class VisaService:
    def __init__(self):
        self.db = db
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
        
        self.common_visa_intents = {
            "requirements": ["hồ sơ", "giấy tờ", "cần gì", "tài liệu", "chuẩn bị gì", "yêu cầu"],
            "cost": ["giá", "phí", "chi phí", "giá cả", "bao nhiêu tiền", "mất bao nhiêu"],
            "process": ["quy trình", "các bước", "thủ tục", "làm sao", "như thế nào", "cách xin"],
            "time": ["thời gian", "mấy ngày", "bao lâu", "khi nào", "mất bao lâu"],
            "success_rate": ["tỷ lệ", "tỷ lệ đậu", "khả năng", "cơ hội", "đậu", "có khó không"],
            "payment": ["thanh toán", "trả tiền", "chuyển khoản", "thẻ tín dụng", "tiền mặt"],
            "terms": ["điều khoản", "chính sách", "quy định", "điều kiện", "cam kết"]
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
    
    def detect_visa_intent(self, message):
        """Phát hiện ý định chính trong câu hỏi về visa"""
        message = message.lower()
        detected_intent = None
        max_score = 0
        
        for intent, keywords in self.common_visa_intents.items():
            for keyword in keywords:
                if keyword in message:
                    count = len(re.findall(rf'\b{keyword}\b', message))
                    score = count * len(keyword)
                    if score > max_score:
                        max_score = score
                        detected_intent = intent
        
        return detected_intent
    
    def extract_visa_info_from_query(self, query):
        """Trích xuất quốc gia và loại visa từ câu hỏi"""
        query = query.lower()
        
        # Lấy danh sách tất cả quốc gia từ database
        all_countries = self.repository.get_all_countries()
        
        # Tìm quốc gia trong câu hỏi bằng fuzzy matching
        country_match = None
        for country in all_countries:
            if country.lower() in query:
                country_match = country
                break
            
            # Kiểm tra các biến thể của tên quốc gia
            aliases = self.repository.get_country_aliases(country)
            for alias in aliases:
                if alias.lower() in query:
                    country_match = country
                    break
        
        # Tìm loại visa trong câu hỏi
        visa_types = ["du lịch", "thương mại", "công tác", "du học", "định cư", "kết hôn"]
        visa_type_match = None
        for visa_type in visa_types:
            if visa_type.lower() in query:
                visa_type_match = visa_type
                break
        
        # Mặc định là du lịch nếu có quốc gia nhưng không có loại visa
        if country_match and not visa_type_match:
            visa_type_match = "du lịch"
        
        return {
            "country": country_match,
            "visa_type": visa_type_match,
            "intent": self.detect_visa_intent(query)
        }
    
    def detect_special_case_query(self, query):
        """Phát hiện các trường hợp đặc biệt trong câu hỏi visa"""
        query = query.lower()
        
        # Các pattern cho các trường hợp đặc biệt
        special_patterns = {
            "no_savings": [
                "không có sổ tiết kiệm", "ko có sổ tiết kiệm", "không có stk", 
                "ko có stk", "chưa có sổ tiết kiệm", "không sổ tiết kiệm",
                "thiếu sổ tiết kiệm", "không đủ tiền", "không đủ số dư",
                "chưa có tiền tiết kiệm"
            ],
            "freelance_job": [
                "công việc tự do", "làm tự do", "không có công ty", "ko có công ty",
                "không đi làm công ty", "không có hợp đồng lao động", "không có hdld",
                "làm freelance", "tự kinh doanh", "kinh doanh tự do", "không có hđlđ"
            ],
            "illegal_stay": [
                "bất hợp pháp", "bat hop phap", "ở lại", "ở lậu", "không giấy phép",
                "quá hạn visa", "qua han visa", "lưu trú quá hạn", "ở lại chui",
                "ở bất hợp pháp", "xin tị nạn", "ti nạn", "nhập cư lậu"
            ],
            "tax_issues": [
                "không đóng thuế", "ko đóng thuế", "chưa đóng thuế", "trốn thuế",
                "không kê khai thuế", "không có thuế", "không đủ thuế", "thiếu thuế"
            ],
            "no_bank_statement": [
                "không sao kê", "ko sao kê", "không có sao kê", "ko có sao kê",
                "không có giấy sao kê", "không chứng minh tài chính", "thiếu sao kê",
                "không có bảng lương", "không chứng minh thu nhập"
            ],
            "proof_request": [
                "có chứng minh công việc", "có làm chứng minh", "giúp chứng minh",
                "hỗ trợ chứng minh", "có làm giấy tờ giả", "giấy tờ ảo", "hỗ trợ hồ sơ",
                "làm giấy tờ", "hồ sơ khó khăn", "giúp làm hồ sơ", "có thể hỗ trợ làm"
            ],
            "previous_rejection": [
                "đã từng bị từ chối", "bị từ chối visa", "đã bị từ chối", "từng bị từ chối", 
                "bị trượt visa", "đã trượt", "bị đánh trượt", "từng bị trượt"
            ],
            "travel_with_family": [
                "đi cùng gia đình", "đi cùng vợ", "đi cùng chồng", "đi với con",
                "đi du lịch gia đình", "đi với gia đình", "đi chung với gia đình"
            ]
        }
        
        # Kiểm tra xem query có match với pattern nào không
        for case_type, patterns in special_patterns.items():
            for pattern in patterns:
                if pattern in query:
                    return case_type
        
        return None
    
    def get_special_case_response(self, case_type=None):
        """Trả về phản hồi phù hợp cho trường hợp đặc biệt"""
        standard_response = ("Dạ, vấn đề này không phải trở ngại lớn đâu ạ! Passport Lounge đã hỗ trợ nhiều khách hàng trong trường hợp tương tự thành công. Vui lòng gọi 1900 636563 hoặc để lại SĐT để được tư vấn phương án phù hợp nhất ạ.")
        
        # Phản hồi tùy theo từng trường hợp
        special_responses = {
            "no_savings": ("Dạ, không có sổ tiết kiệm không phải là vấn đề lớn. Passport Lounge có nhiều giải pháp thay thế hiệu quả. Vui lòng gọi 1900 636563 hoặc để lại SĐT để được tư vấn ngay ạ."),
                          
            "freelance_job": ("Dạ, nghề tự do vẫn xin visa được nếu có phương án chứng minh phù hợp. Passport Lounge đã hỗ trợ thành công nhiều khách hàng tương tự. Vui lòng gọi 1900 636563 hoặc để lại SĐT ạ."),
                             
            "illegal_stay": ("Dạ, đây là trường hợp cần được tư vấn riêng. Để đảm bảo quyền lợi cho quý khách, vui lòng gọi 1900 636563 hoặc để lại SĐT để được chuyên viên cao cấp tư vấn kín ạ."),
                           
            "tax_issues": ("Dạ, vấn đề thuế hoàn toàn có giải pháp phù hợp. Passport Lounge đã hỗ trợ nhiều trường hợp tương tự. Vui lòng gọi 1900 636563 hoặc để lại SĐT để được tư vấn ạ."),
                         
            "no_bank_statement": ("Dạ, không có sao kê ngân hàng vẫn có thể xin visa. Passport Lounge có nhiều phương án thay thế hiệu quả. Vui lòng gọi 1900 636563 hoặc để lại SĐT để được tư vấn ạ."),
                                
            "proof_request": ("Dạ, Passport Lounge chỉ hỗ trợ hồ sơ hợp pháp và đầy đủ. Chúng tôi có nhiều phương án chứng minh phù hợp với từng trường hợp. Vui lòng gọi 1900 636563 hoặc để lại SĐT ạ."),
                            
            "previous_rejection": ("Dạ, từng bị từ chối vẫn có thể đậu visa nếu chuẩn bị đúng cách. Passport Lounge đã giúp nhiều khách hàng thành công sau khi từng bị từ chối. Vui lòng gọi 1900 636563 ạ."),
                                 
            "travel_with_family": ("Dạ, đi du lịch gia đình cần lưu ý một số điểm đặc biệt trong hồ sơ. Passport Lounge sẽ hướng dẫn cách chuẩn bị tối ưu. Vui lòng gọi 1900 636563 hoặc để lại SĐT ạ.")
        }
        
        if case_type in special_responses:
            return special_responses[case_type]
        
        return standard_response
    
    def collect_customer_contact(self, user_query, user_id):
        """Thu thập thông tin liên hệ của khách hàng"""
        phone_pattern = r'(0[0-9]{9,10})|(\+84[0-9]{9,10})'
        phone_matches = re.findall(phone_pattern, user_query)
        
        phone_number = None
        if phone_matches:
            phone_number = phone_matches[0][0] or phone_matches[0][1]
            
        if phone_number:
            try:
                # Lưu thông tin khách hàng vào database
                customer_data = {
                    "user_id": user_id,
                    "phone": phone_number,
                    "source": "zalo_chat",
                    "query": user_query,
                    "status": "new_lead",
                    "created_at": datetime.now()
                }
                self.db.leads.insert_one(customer_data)
                
                return {
                    "success": True,
                    "message": f"Cảm ơn đã để lại số {phone_number}. Chuyên viên visa Passport Lounge sẽ gọi lại tư vấn cho bạn trong thời gian sớm nhất!"
                }
            except Exception as e:
                print(f"Error collecting customer contact: {e}")
                
        return None
    
    def answer_visa_question(self, user_query, user_id=None):
        """Trả lời câu hỏi về visa dựa trên ý định và thông tin trích xuất"""
        # Kiểm tra nếu người dùng đang cung cấp số điện thoại
        contact_response = None
        if user_id:
            contact_response = self.collect_customer_contact(user_query, user_id)
            if contact_response:
                return contact_response
                
        # Kiểm tra nếu là trường hợp đặc biệt
        special_case = self.detect_special_case_query(user_query)
        if (special_case):
            return {
                "success": True,
                "message": self.get_special_case_response(special_case),
                "type": "special_case"
            }
            
        # Xử lý câu hỏi thông thường nếu không phải case đặc biệt
        extracted_info = self.extract_visa_info_from_query(user_query)
        
        if not extracted_info["country"]:
            return {
                "success": False,
                "message": "Vui lòng cho biết bạn cần tìm hiểu về visa của quốc gia nào?"
            }
        
        # Tìm thông tin visa từ database
        visas = self.repository.find_by_country_and_type(
            extracted_info["country"],
            extracted_info["visa_type"]
        )
        
        if not visas:
            return {
                "success": False,
                "message": f"Xin lỗi, hiện tại chúng tôi không có thông tin về visa {extracted_info['visa_type'] or ''} cho {extracted_info['country']}."
            }
        
        # Nếu có intent cụ thể, trả lời dựa vào intent
        if extracted_info["intent"] and len(visas) == 1:
            return self.format_visa_response_by_intent(
                visas[0],
                extracted_info["intent"],
                user_query
            )
        
        # Nếu không có intent cụ thể hoặc có nhiều loại visa
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
    
    def format_visa_response_by_intent(self, visa, intent, original_query):
        """Định dạng phản hồi dựa vào ý định của người dùng"""
        if intent == "requirements":
            return self.format_requirements_response(visa)
        elif intent == "cost":
            return self.format_cost_response(visa)
        elif intent == "process":
            return self.format_process_response(visa)
        elif intent == "time":
            return self.format_time_response(visa)
        elif intent == "success_rate":
            return self.format_success_rate_response(visa)
        elif intent == "payment":
            return self.format_payment_response(visa)
        elif intent == "terms":
            return self.format_terms_response(visa)
        else:
            # Mặc định trả về thông tin tổng quát
            return {
                "success": True,
                "data": visa,
                "type": "single"
            }
    
    def format_requirements_response(self, visa):
        """Định dạng phản hồi về yêu cầu hồ sơ"""
        response = f"📋 HỒ SƠ XIN VISA {visa['visa_type'].upper()} {visa['country'].upper()}\n\n"
        
        if "requirements" in visa:
            if isinstance(visa["requirements"], dict):
                for category, docs in visa["requirements"].items():
                    if category == "personal_docs":
                        response += "▶️ Hồ sơ nhân thân:\n"
                    elif category == "financial_docs":
                        response += "▶️ Hồ sơ chứng minh tài sản:\n"
                    elif category == "employment_docs":
                        response += "▶️ Hồ sơ công việc & thu nhập:\n"
                    elif category == "travel_docs":
                        response += "▶️ Giấy tờ chuyến đi:\n"
                    else:
                        response += f"▶️ {category}:\n"
                    
                    for i, doc in enumerate(docs, 1):
                        response += f"{i}. {doc}\n"
                    response += "\n"
            else:
                for i, req in enumerate(visa["requirements"], 1):
                    response += f"{i}. {req}\n"
        
        response += f"\n📞 Để được tư vấn chi tiết, vui lòng gọi 1900 636563"
        
        return {
            "success": True,
            "message": response,
            "type": "intent_response"
        }
    
    # Tương tự cho các hàm format khác (cost, process, time, etc.)
    
    def format_visa_info_message(self, visa):
        """Định dạng thông tin visa để hiển thị cho người dùng"""
        response = f"🛂 VISA {visa['visa_type'].upper()} {visa['country'].upper()}\n\n"
        response += f"💰 Giá: ${visa['price']} USD\n"
        response += f"⏱️ Thời gian xử lý: {visa['processing_time']}\n"
        
        if "success_rate" in visa and visa["success_rate"]:
            response += f"✅ Tỷ lệ đậu visa: {visa['success_rate']}%\n\n"
        
        response += "✨ QUYỀN LỢI:\n"
        if "benefits" in visa and visa["benefits"]:
            for benefit in visa["benefits"]:
                response += f"✓ {benefit}\n"
        
        response += "\n📋 QUY TRÌNH XIN VISA:\n"
        if "process_steps" in visa and visa["process_steps"]:
            for i, step in enumerate(visa["process_steps"], 1):
                response += f"{i}. {step['name']}: {step['description']}\n"
        
        response += "\n💼 CHI PHÍ DỊCH VỤ:\n"
        if "costs" in visa and "options" in visa["costs"]:
            for option in visa["costs"]["options"]:
                response += f"- {option['type']}: ${option['price']} USD ({option['duration']})\n"
        
        response += f"\n📞 Hotline hỗ trợ: 1900 636563\n"
        
        return response

    def search_visa_info(self, country=None, visa_type=None):
        """Search for visa information based on country and type"""
        query = {}
        
        if country:
            country = country.lower().strip()
            query["$or"] = [
                {"country": {"$regex": country, "$options": "i"}},
                {"country_aliases": {"$elemMatch": {"$regex": country, "$options": "i"}}}
            ]
            
        if visa_type:
            visa_type = visa_type.lower().strip()
            if "$or" not in query:
                query["$or"] = []
            
            query["$or"].extend([
                {"visa_type": {"$regex": visa_type, "$options": "i"}},
                {"type_aliases": {"$elemMatch": {"$regex": visa_type, "$options": "i"}}}
            ])
            
        return list(self.db.visas.find(query))
        
    def _calculate_match_score(self, visa, query):
        """Calculate how well a visa matches the query"""
        query = query.lower().strip()
        scores = []
        
        # Check country match
        country_score = fuzz.partial_ratio(query, visa.get('country', '').lower())
        for alias in visa.get('country_aliases', []):
            alias_score = fuzz.partial_ratio(query, alias.lower())
            country_score = max(country_score, alias_score)
        scores.append(country_score)
        
        # Check visa type match
        type_score = fuzz.partial_ratio(query, visa.get('visa_type', '').lower())
        for alias in visa.get('type_aliases', []):
            alias_score = fuzz.partial_ratio(query, alias.lower())
            type_score = max(type_score, alias_score)
        scores.append(type_score)
        
        # Return weighted average
        return 0.7 * country_score + 0.3 * type_score
        
    def format_visa_info(self, visa):
        """Format visa information for display to users"""
        if not visa:
            return "Không tìm thấy thông tin visa phù hợp."
            
        response = f"🛂 VISA {visa['visa_type'].upper()} {visa['country'].upper()}\n\n"
        response += f"💰 Giá: ${visa['price']} USD\n"
        response += f"⏱️ Thời gian xử lý: {visa['processing_time']}\n"
        
        if "success_rate" in visa:
            response += f"✅ Tỷ lệ đậu visa: {visa['success_rate']}%\n\n"
            
        response += "📋 HỒ SƠ CẦN THIẾT:\n"
        for category, docs in visa.get("requirements", {}).items():
            if isinstance(docs, list):
                for doc in docs:
                    response += f"• {doc}\n"
            elif isinstance(docs, dict):
                for key, items in docs.items():
                    response += f"\n{key.capitalize()}:\n"
                    for item in items:
                        response += f"• {item}\n"
                        
        response += "\n💼 CHI PHÍ:\n"
        for option in visa.get("costs", {}).get("options", []):
            response += f"• {option['type']}: ${option['price']} USD ({option['duration']})\n"
            
        response += f"\n📞 Hotline hỗ trợ: 1900 636563\n"
        response += f"\nĐể đặt dịch vụ visa, vui lòng trả lời 'Đặt visa {visa['country']}'"
        
        return response

    def answer_specific_visa_query(self, query, visa_data):
        """Provide focused answers to specific visa questions using available data"""
        query_lower = query.lower()
        
        # Detect intent patterns in user's question
        intent = None
        if any(word in query_lower for word in ["hồ sơ", "giấy tờ", "cần gì", "chuẩn bị"]):
            intent = "requirements"
        elif any(word in query_lower for word in ["giá", "phí", "chi phí", "bao nhiêu tiền"]):
            intent = "cost"
        elif any(word in query_lower for word in ["thời gian", "mấy ngày", "bao lâu", "khi nào"]):
            intent = "processing_time"
        elif any(word in query_lower for word in ["quy trình", "các bước", "thủ tục", "làm sao"]):
            intent = "process"
        elif any(word in query_lower for word in ["tỷ lệ", "khả năng", "cơ hội", "có khó không"]):
            intent = "success_rate"
        
        # Format response based on detected intent
        if intent == "requirements":
            return self._format_requirements_response(visa_data)
        elif intent == "cost":
            return self._format_cost_response(visa_data)
        elif intent == "processing_time":
            return self._format_time_response(visa_data)  
        elif intent == "process":
            return self._format_process_response(visa_data)
        elif intent == "success_rate":
            return self._format_success_rate_response(visa_data)
        else:
            return self._format_general_response(visa_data)
    
    def _format_requirements_response(self, visa):
        """Format detailed visa requirements response"""
        response = f"📋 HỒ SƠ XIN VISA {visa['visa_type'].upper()} {visa['country'].upper()}:\n\n"
        
        if "requirements" in visa:
            if isinstance(visa["requirements"], dict):
                for category, docs in visa["requirements"].items():
                    if isinstance(docs, list):
                        if category == "personal_docs":
                            response += "▶️ Hồ sơ nhân thân:\n"
                        elif category == "financial_docs":
                            response += "▶️ Hồ sơ chứng minh tài sản:\n"
                        elif category == "employment_docs":
                            response += "▶️ Hồ sơ công việc & thu nhập:\n"
                        elif category == "travel_docs":
                            response += "▶️ Giấy tờ chuyến đi:\n"
                        else:
                            response += f"▶️ {category}:\n"
                        
                        for i, doc in enumerate(docs, 1):
                            response += f"{i}. {doc}\n"
                        response += "\n"
                    elif isinstance(docs, dict):
                        response += f"▶️ {category}:\n"
                        for subcat, items in docs.items():
                            response += f"- {subcat.capitalize()}:\n"
                            for i, item in enumerate(items, 1):
                                response += f"  {i}. {item}\n"
                        response += "\n"
            else:
                for i, req in enumerate(visa["requirements"], 1):
                    response += f"{i}. {req}\n"
        
        response += f"\n📞 Để được tư vấn chi tiết về hồ sơ, vui lòng gọi hotline 1900 636563"
        return response
    
    # Similar implementation for other intents (_format_cost_response, _format_time_response, etc.)

# Khởi tạo service
visa_service = VisaService()