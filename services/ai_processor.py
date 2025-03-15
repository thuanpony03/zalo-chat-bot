import google.generativeai as genai
from config import Config
import asyncio
from datetime import datetime, timedelta
import re
import logging

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIProcessor:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.visa_data = {}  # Cache dữ liệu visa
        self.last_refresh = None  # Thời gian làm mới cache cuối cùng
        
    async def load_visa_data(self, country=None):
        """Tải dữ liệu visa từ database, có thể chỉ tải cho một quốc gia cụ thể"""
        from services.database import db
        try:
            if self.last_refresh and (datetime.now() - self.last_refresh) < timedelta(hours=24) and not country:
                logger.info("Sử dụng dữ liệu visa từ cache")
                return True
                
            query = {} if not country else {"country": {"$regex": f"^{country}$", "$options": "i"}}
            visas = list(db.get_collection("visas").find(query))
            logger.info(f"Tìm thấy {len(visas)} bản ghi visa trong database")
            
            for visa in visas:
                visa['_id'] = str(visa['_id'])
                country_key = visa.get('country', '').lower()
                if country_key not in self.visa_data:
                    self.visa_data[country_key] = []
                self.visa_data[country_key].append(visa)
                
            if not country:
                self.last_refresh = datetime.now()
            logger.info(f"Đã tải visa cho các quốc gia: {list(self.visa_data.keys())}")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi tải dữ liệu visa: {e}")
            return False

    async def process_visa_query(self, user_query, user_context=None):
        """Xử lý câu hỏi về visa với LLM"""
        try:
            if not self.visa_data:
                await self.load_visa_data()
                
            context_to_return = user_context or {}
            
            # Save original query if this is a new conversation
            if not user_context or 'previous_messages' not in user_context or len(user_context.get('previous_messages', [])) <= 1:
                context_to_return['original_query'] = user_query
            
            if user_query.lower() in ["reset", "restart", "bắt đầu lại", "khởi động lại"]:
                return "Đã reset trạng thái hội thoại. Bạn có thể bắt đầu lại với một câu hỏi mới.", {}

            # Kiểm tra nếu có số điện thoại trong tin nhắn của khách
            phone_number = self._extract_phone_number(user_query)
            if phone_number:
                context_to_return['customer_phone'] = phone_number
                # Lưu thông tin khách hàng vào database
                await self._save_customer_contact(context_to_return.get('customer_name', ''), 
                                                phone_number, 
                                                context_to_return.get('country', ''),
                                                user_context.get('user_id') if user_context else None)
                return f"Cảm ơn đã để lại số {phone_number}. Tư vấn viên của Passport Lounge sẽ liên hệ với bạn trong thời gian sớm nhất!", context_to_return

            # Trích xuất tên khách hàng nếu có
            customer_name = self._extract_customer_name(user_query)
            if customer_name and not context_to_return.get('customer_name'):
                context_to_return['customer_name'] = customer_name

            # Phát hiện nếu khách hàng đang lo lắng về điều kiện đặc biệt
            has_concerns = self._detect_customer_concerns(user_query)
            if has_concerns:
                context_to_return['has_special_concerns'] = True
                
                # Check if this is a special case that should be directed to hotline
                from services.visa_service import visa_service
                special_case = visa_service.detect_special_case_query(user_query)
                if special_case:
                    context_to_return['special_case'] = special_case
                    response = visa_service.get_special_case_response(special_case)
                    return response, context_to_return
            
            current_country = self._extract_country_from_query(user_query)
            family_travel = self._extract_family_travel(user_query)
            stay_duration = self._extract_stay_duration(user_query)
            
            if family_travel:
                context_to_return['family_travel'] = True
            if stay_duration:
                context_to_return['stay_duration'] = stay_duration
                
            country = None
            if current_country:
                country = current_country
                context_to_return['country'] = country
                if country.lower() not in self.visa_data:
                    await self.load_visa_data(country)
                logger.info(f"Quốc gia mới từ câu hỏi: {country}")
            elif user_context and 'country' in user_context:
                country = user_context['country']
                logger.info(f"Sử dụng quốc gia từ context: {country}")
            
            visa_info = None
            if country and country.lower() in self.visa_data:
                visa_info = self._select_best_visa(country.lower(), context_to_return)
            
            context_str = ""
            if user_context and 'previous_messages' in user_context:
                messages = user_context['previous_messages'][-3:]
                if messages:
                    context_str = "Lịch sử hội thoại:\n"
                    for msg in messages:
                        role = "Khách hàng" if msg['sender'] == 'user' else "Tư vấn viên"
                        context_str += f"{role}: {msg['message']}\n"
            
            prompt = self._build_visa_prompt(user_query, visa_info, context_str, context_to_return)
            response = await self._generate_response(prompt)
            return response, context_to_return
            
        except Exception as e:
            logger.error(f"Lỗi trong process_visa_query: {e}", exc_info=True)
            return "Xin lỗi, có lỗi xảy ra. Vui lòng liên hệ hotline 1900 636563 để được hỗ trợ.", user_context or {}

    def _extract_country_from_query(self, query):
        """Trích xuất quốc gia từ câu hỏi"""
        if not query:
            return None
            
        query_lower = query.lower()
        
        # Bản đồ từ khóa quốc gia - Mở rộng để bao phủ nhiều quốc gia hơn
        country_keywords = {
            "trung quốc": ["trung quốc", "trung quoc", "china", "tq", "trung"],
            "ấn độ": ["ấn độ", "an do", "india", "ấn", "in độ", "in do"],
            "hàn quốc": ["hàn quốc", "han quoc", "korea", "hàn", "han"],
            "nhật bản": ["nhật bản", "nhat ban", "japan", "nhật", "nhat"],
            "hongkong": ["hongkong", "hong kong", "hồng kông", "hk", "hong", "hồng"],
            "đài loan": ["đài loan", "dai loan", "taiwan", "đài", "dai"],
            "nga": ["nga", "russia", "liên bang nga", "lien bang nga", "russian"],
            "úc": ["úc", "australia", "uc", "au", "nước úc"],
            "mỹ": ["mỹ", "usa", "america", "united states", "my", "hoa kỳ"],
            "anh": ["anh", "uk", "england", "anh quốc", "british"],
            "canada": ["canada"]
        }
        
        # Kiểm tra từng từ khóa trong text
        for country, keywords in country_keywords.items():
            for keyword in keywords:
                # Kiểm tra từ đầy đủ để tránh nhận diện nhầm
                if keyword in query_lower.split():
                    return country
        
        # Nếu không tìm thấy từ khóa cụ thể, thử tìm trong database
        try:
            for country in self.visa_data.keys():
                if country in query_lower:
                    return country
        except:
            pass
            
        return None

    def _extract_family_travel(self, query):
        """Trích xuất nhu cầu đi du lịch gia đình"""
        query_lower = query.lower()
        family_keywords = ["gia đình", "vợ", "chồng", "con", "con trai", "con gái", 
                          "ba mẹ", "bố mẹ", "cha mẹ", "cả nhà"]
        return any(keyword in query_lower for keyword in family_keywords)
        
    def _extract_stay_duration(self, query):
        """Trích xuất thời gian lưu trú"""
        query_lower = query.lower()
        duration_matches = re.findall(r'(\d+)\s*(ngày|tuần|tháng|năm|thang|nam|tuan)', query_lower)
        
        if duration_matches:
            number, unit = duration_matches[0]
            number = int(number)
            days = number * (30 if unit in ["tháng", "thang"] else 7 if unit in ["tuần", "tuan"] else 365 if unit in ["năm", "nam"] else 1)
            return {"value": number, "unit": unit, "days": days}
            
        long_stay_keywords = ["lâu hơn", "dài hạn", "ở lâu", "nhiều ngày", "nhiều tháng"]
        if any(keyword in query_lower for keyword in long_stay_keywords):
            return {"long_stay": True}
        return None

    def _select_best_visa(self, country, context):
        """Chọn visa phù hợp dựa trên context"""
        visas = self.visa_data.get(country, [])
        if not visas:
            return None
            
        # Nếu khách hàng có trường hợp đặc biệt, ưu tiên thông tin visa có requirements đầy đủ
        if context.get('has_special_concerns', False):
            for visa in visas:
                if "requirements" in visa and isinstance(visa["requirements"], dict) and len(visa["requirements"]) > 0:
                    return visa
            
        best_visa = visas[0]
        if "stay_duration" in context and context["stay_duration"].get("days"):
            target_days = context["stay_duration"]["days"]
            for visa in visas:
                for opt in visa.get("costs", {}).get("options", []):
                    opt_days = self._convert_duration_to_days(opt.get("duration", ""))
                    if opt_days >= target_days:
                        best_visa = visa
                        break
        elif "family_travel" in context and context["family_travel"]:
            best_visa = min(visas, key=lambda v: v.get("price", float('inf')))
        return best_visa

    def _convert_duration_to_days(self, duration_str):
        """Chuyển đổi chuỗi thời hạn visa thành số ngày"""
        if not duration_str:
            return 0
            
        duration_str = duration_str.lower()
        if "ngày" in duration_str:
            try:
                return int(re.search(r'(\d+)', duration_str).group(1))
            except:
                return 30
        elif "tháng" in duration_str:
            try:
                months = int(re.search(r'(\d+)', duration_str).group(1))
                return months * 30
            except:
                return 90
        elif "năm" in duration_str:
            try:
                years = int(re.search(r'(\d+)', duration_str).group(1))
                return years * 365
            except:
                return 365
        # Mặc định trả về 90 ngày nếu không xác định được
        return 90

    async def _generate_response(self, prompt):
        """Gọi Gemini để tạo phản hồi"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: self.model.generate_content(prompt))
            result = response.text.strip()
            
            # Đảm bảo độ dài phù hợp - không quá ngắn
            if len(result) < 100 and not "số điện thoại" in result.lower():
                result += " Anh/chị vui lòng để lại số điện thoại để tư vấn viên liên hệ hỗ trợ chi tiết nhé!"
                
            return result
        except Exception as e:
            logger.error(f"Lỗi khi tạo phản hồi: {e}")
            return "Xin lỗi, tôi không thể trả lời vào lúc này. Vui lòng gọi 1900 636563 để được hỗ trợ."

    def _build_visa_prompt(self, query, visa_info, context_str="", user_context=None):
        """Xây dựng prompt hiệu quả cho visa"""
        prompt = """Bạn là tư vấn viên visa chuyên nghiệp tại Passport Lounge với giọng điệu tự nhiên giống người.
CẢNH BÁO QUAN TRỌNG: Phản hồi của bạn PHẢI NGẮN GỌN (tối đa 4-5 câu, khoảng 300-400 ký tự).
KHÔNG liệt kê chi tiết giấy tờ hay quy trình cụ thể.
Giọng điệu thân thiện, đồng cảm và tự nhiên.
Khi nói về giá, LUÔN sử dụng khoảng giá (ví dụ: "khoảng 3-4 triệu") thay vì số chính xác.
"""
        # Thêm thông tin về ngữ cảnh hội thoại trước đó nếu có
        if context_str:
            prompt += f"\nNgữ cảnh cuộc hội thoại:\n{context_str}\n"

        # Thêm thông tin về sản phẩm visa cụ thể nếu có
        if visa_info:
            country_name = visa_info.get('country', '')
            prompt += f"\nDữ liệu sản phẩm visa {country_name}:\n"
            prompt += f"- Loại visa: {visa_info.get('visa_type', '')} {visa_info.get('visa_method', '')}\n"
            price = visa_info.get('price', '')
            # Tính giá thấp hơn khoảng 5-10%
            discounted_price = int(price * 0.92) if price else 0  # Giảm 8%
            price_vnd = int(price * 25000) if price else 0
            discounted_price_vnd = int(discounted_price * 25000) if discounted_price else 0
            
            # Làm tròn giá thành khoảng giá
            price_range_low = int(discounted_price_vnd * 0.9 / 1000000)
            price_range_high = int(discounted_price_vnd * 1.1 / 1000000)
            
            prompt += f"- Giá thật: ${price} USD (khoảng {price_vnd:,} VND)\n"
            prompt += f"- Giá báo khách: khoảng {price_range_low}-{price_range_high} triệu VND\n"
            prompt += f"- Thời gian xử lý: {visa_info.get('processing_time', '')}\n"
        else:
            prompt += "\nKhông có dữ liệu cụ thể về visa này trong cơ sở dữ liệu. Trả lời ngắn gọn và hỏi thêm thông tin để hiểu nhu cầu khách hàng."

        # Xác định xem người dùng có đang lo lắng về điều kiện đặc biệt không
        has_concerns = user_context and user_context.get('has_special_concerns', False)
        
        # Hướng dẫn đặc biệt khi khách hàng có trường hợp đặc biệt
        if has_concerns:
            prompt += """
\nKhách hàng đang lo lắng về một số điều kiện đặc biệt. Khi trả lời:
1. Thể hiện sự đồng cảm và sự tự tin giải quyết.
2. Đề cập rằng Passport Lounge có giải pháp cho trường hợp đặc biệt này.
3. Nói đã giúp nhiều khách hàng tương tự thành công.
4. ĐỀ CẬP RẰNG: Để tư vấn chi tiết cho trường hợp này, cần liên hệ hotline 1900 636563 hoặc để lại SĐT.
"""

        # Thêm câu hỏi của người dùng
        prompt += f"\nCâu hỏi hiện tại: {query}\n"
        
        # Hướng dẫn cho AI
        prompt += """
HƯỚNG DẪN PHẢN HỒI:
- Trả lời với độ dài vừa đủ (4-5 câu ngắn) để cung cấp thông tin hữu ích.
- Thể hiện sự hiểu biết chuyên sâu và đồng cảm với khách hàng.
- Trả lời cụ thể nhưng không đi vào chi tiết kỹ thuật.
- Khi được hỏi về giá, LUÔN đưa ra khoảng giá (không nêu số chính xác).
- THƯỜNG XUYÊN KẾT THÚC các câu trả lời bằng câu hỏi đơn giản như "Anh/chị còn thắc mắc gì nữa không?" hoặc "Anh/chị quan tâm đến điều gì khác không?"

HƯỚNG DẪN VỀ LIÊN HỆ:
- Trường hợp khách cần hỗ trợ phức tạp hoặc quan tâm đến giá/chi tiết dịch vụ, khuyến khích để lại SĐT hoặc gọi hotline: "Anh/chị có thể để lại SĐT hoặc gọi 1900 636563 để được hỗ trợ tốt nhất."
- Trường hợp khách hỏi về hồ sơ phức tạp, tài chính, công việc: đề cập hotline 1900 636563 hoặc gợi ý để lại SĐT.
- Đề xuất liên hệ một cách tự nhiên, không gây áp lực, chẳng hạn "Để tư vấn chi tiết hơn, anh/chị có thể để lại SĐT hoặc gọi hotline 1900 636563 ạ".
"""

        return prompt

    async def _save_customer_contact(self, name, phone, country, user_id):
        """Lưu thông tin liên hệ của khách hàng vào database với nhiều context hơn"""
        from services.database import db
        try:
            # Tạo collection 'leads' nếu chưa tồn tại
            if 'leads' not in db.db.list_collection_names():
                db.db.create_collection('leads')
                logger.info("Đã tạo collection 'leads'")
            
            # Lấy thêm thông tin từ context lưu trữ trong database
            user_context = {}
            if user_id:
                users_collection = db.get_collection("users")
                user_data = users_collection.find_one({"user_id": user_id})
                if user_data and "context" in user_data:
                    user_context = user_data["context"]
                    
            # Trích xuất các thông tin quan trọng từ context
            special_concerns = user_context.get('has_special_concerns', False)
            special_case = user_context.get('special_case', None)
            family_travel = user_context.get('family_travel', False)
            stay_duration = user_context.get('stay_duration', None)
            
            # Lấy tin nhắn gần đây để hiểu nhu cầu của khách
            recent_messages = []
            if user_id:
                messages_collection = db.get_collection("messages")
                recent_msgs = list(messages_collection.find(
                    {"user_id": user_id},
                    {"_id": 0, "message": 1, "sender": 1, "timestamp": 1}
                ).sort("timestamp", -1).limit(5))
                
                recent_messages = [msg for msg in recent_msgs]
            
            # Xây dựng mô tả về nhu cầu của khách
            customer_needs = []
            if country:
                customer_needs.append(f"Quan tâm đến visa {country}")
            if special_case:
                case_descriptions = {
                    "no_savings": "Không có sổ tiết kiệm",
                    "freelance_job": "Làm việc tự do/freelance",
                    "illegal_stay": "Có vấn đề về lưu trú/tị nạn",
                    "tax_issues": "Có vấn đề về thuế",
                    "no_bank_statement": "Không có sao kê ngân hàng",
                    "proof_request": "Cần hỗ trợ chứng minh tài chính/việc làm",
                    "previous_rejection": "Đã từng bị từ chối visa",
                    "travel_with_family": "Đi cùng gia đình"
                }
                customer_needs.append(case_descriptions.get(special_case, f"Vấn đề đặc biệt: {special_case}"))
            if family_travel:
                customer_needs.append("Đi du lịch cùng gia đình")
            if stay_duration:
                if isinstance(stay_duration, dict) and "days" in stay_duration:
                    customer_needs.append(f"Thời gian lưu trú: {stay_duration['days']} ngày")
                elif isinstance(stay_duration, dict) and "long_stay" in stay_duration:
                    customer_needs.append("Dự định lưu trú dài hạn")
            
            # Tạo dữ liệu khách hàng với nhiều context hơn
            customer_data = {
                "name": name,
                "phone": phone,
                "country_interest": country,
                "zalo_user_id": user_id,
                "source": "zalo_bot",
                "status": "new_lead",
                "created_at": datetime.now(),
                "customer_needs": customer_needs,
                "special_concerns": special_concerns,
                "special_case_type": special_case,
                "recent_conversation": recent_messages,
                "original_query": user_context.get('original_query', None) if user_context else None
            }
            
            # Sử dụng chính xác phương thức insert_one từ collection
            db.db.leads.insert_one(customer_data)
            logger.info(f"Đã lưu thông tin khách hàng: {phone} với {len(customer_needs)} nhu cầu")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi lưu thông tin khách hàng: {e}")
            return False

    def _extract_phone_number(self, text):
        """Trích xuất số điện thoại từ text"""
        if not text:
            return None
            
        # Pattern cho số điện thoại Việt Nam: 10-11 số, bắt đầu bằng 0 hoặc +84
        phone_pattern = r'(0[0-9]{9,10})|(\+84[0-9]{9,10})'
        matches = re.findall(phone_pattern, text)
        
        if matches:
            for match in matches:
                for group in match:
                    if group:
                        return group
        return None

    def _extract_customer_name(self, text):
        """Trích xuất tên khách hàng từ text"""
        name_patterns = [
            r'(?:tên|tôi|mình|tui|em|anh|chị) (?:là|tên là|tên|gọi là) ([A-Za-zÀ-ỹ\s]{2,30})',
            r'(?:tên|họ tên|họ và tên)[:\s]+([A-Za-zÀ-ỹ\s]{2,30})',
        ]
        
        for pattern in name_patterns:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                return matches.group(1).strip()
        return None

    def _detect_customer_concerns(self, query):
        """Phát hiện các lo ngại đặc biệt của khách hàng"""
        query = query.lower()
        
        # Mở rộng các pattern để phát hiện các trường hợp đặc biệt
        special_concern_patterns = [
            # Financial concerns
            "không có sổ tiết kiệm", "ko có sổ", "chưa có sổ", "không đủ tiền",
            "không đủ tài chính", "không chứng minh được tài chính",
            
            # Employment concerns
            "công việc tự do", "làm tự do", "không có công ty", "ko có công ty",
            "không đi làm công ty", "không có hợp đồng lao động", "không có hdld",
            "làm freelance", "tự kinh doanh", "kinh doanh tự do", "không có hđlđ",
            
            # Immigration/legal concerns
            "bất hợp pháp", "bat hop phap", "ở lại", "ở lậu", "không giấy phép",
            "quá hạn visa", "qua han visa", "lưu trú quá hạn", "ở lại chui",
            "ở bất hợp pháp", "xin tị nạn", "ti nạn", "nhập cư lậu",
            
            # Document concerns
            "không sao kê", "ko sao kê", "không có sao kê", "ko có sao kê",
            "không có giấy sao kê", "không chứng minh tài chính", "thiếu sao kê",
            "không có bảng lương", "không chứng minh thu nhập",
            
            # Previous rejection concerns
            "đã từng bị từ chối", "bị từ chối visa", "đã bị từ chối", "từng bị từ chối", 
            "bị trượt visa", "đã trượt", "bị đánh trượt", "từng bị trượt",
            
            # Quick processing concerns
            "cần gấp", "khẩn", "nhanh", "sớm", "tuần sau", "vài ngày tới",
            "cuối tháng", "gấp rút", "express", "cấp tốc"
        ]
        
        for pattern in special_concern_patterns:
            if pattern in query:
                return True
                
        return False

ai_processor = AIProcessor()