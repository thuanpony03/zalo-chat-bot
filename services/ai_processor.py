#!/usr/bin/env python3
"""
AI Processor for handling visa queries using Google Gemini API.
"""
import google.generativeai as genai
import asyncio
import logging
import re
from datetime import datetime, timedelta

from config import Config

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIProcessor:
    def __init__(self):
        """Initialize AIProcessor with Gemini API and cache."""
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.visa_data = {}  # Cache dữ liệu visa
        self.last_refresh = None  # Thời gian làm mới cache cuối cùng
        self.conversation_context = {}  # Theo dõi ngữ cảnh hội thoại

    async def load_visa_data(self, country=None):
        """Load visa data from database, optionally for a specific country."""
        try:
            from services.database import db
            if (self.last_refresh and (datetime.now() - self.last_refresh) < timedelta(hours=24) and not country):
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
        """Process visa query and return response with context."""
        try:
            if not self.visa_data:
                await self.load_visa_data()
            context_to_return = user_context or {}
            self.conversation_context = context_to_return.copy()

            # Lưu câu hỏi gốc nếu là hội thoại mới
            if (not user_context or 'previous_messages' not in user_context or 
                len(user_context.get('previous_messages', [])) <= 1):
                context_to_return['original_query'] = user_query

            # Reset hội thoại
            if user_query.lower() in ["reset", "restart", "bắt đầu lại", "khởi động lại"]:
                if user_context and 'user_id' in user_context:
                    from services.database import db
                    users_collection = db.get_collection("users")
                    users_collection.update_one(
                        {"user_id": user_context['user_id']},
                        {"$set": {"context": {}}},
                        upsert=True
                    )
                return "Đã reset trạng thái hội thoại. Bạn có thể bắt đầu lại với một câu hỏi mới.", {}

            # Kiểm tra số điện thoại
            phone_number = self._extract_phone_number(user_query)
            if phone_number:
                context_to_return['customer_phone'] = phone_number
                customer_name = context_to_return.get('customer_name', '') or self._extract_customer_name(user_query)
                user_id = user_context.get('user_id') if user_context else None
                await self._save_customer_contact(
                    customer_name, phone_number, context_to_return.get('country', ''),
                    user_id, context_to_return
                )
                if user_id:
                    from services.database import db
                    users_collection = db.get_collection("users")
                    users_collection.update_one(
                        {"user_id": user_id},
                        {"$set": {"context": context_to_return}},
                        upsert=True
                    )
                return (
                    f"Cảm ơn đã để lại số {phone_number}. "
                    "Tư vấn viên của Passport Lounge sẽ liên hệ với bạn trong thời gian sớm nhất!",
                    context_to_return
                )

            # Trích xuất tên khách hàng
            customer_name = self._extract_customer_name(user_query)
            if customer_name and not context_to_return.get('customer_name'):
                context_to_return['customer_name'] = customer_name

            # Phát hiện lo ngại đặc biệt
            has_concerns = self._detect_customer_concerns(user_query)
            if has_concerns:
                context_to_return['has_special_concerns'] = True
                from services.visa_service import visa_service
                special_case = visa_service.detect_special_case_query(user_query)
                if special_case:
                    context_to_return['special_case'] = special_case
                    response = visa_service.get_special_case_response(special_case)
                    if user_context and 'user_id' in user_context:
                        from services.database import db
                        users_collection = db.get_collection("users")
                        users_collection.update_one(
                            {"user_id": user_context['user_id']},
                            {"$set": {"context": context_to_return}},
                            upsert=True
                        )
                    return response, context_to_return

            current_country = self._extract_country_from_query(user_query)
            family_travel = self._extract_family_travel(user_query)
            stay_duration = self._extract_stay_duration(user_query)

            if family_travel:
                context_to_return['family_travel'] = True
            if stay_duration:
                context_to_return['stay_duration'] = stay_duration

            # Cập nhật phát hiện quốc gia với AI
            logger.info(f"Đang xử lý query: '{user_query}'")
            potential_country = await self._extract_country_with_ai(user_query)
            logger.info(f"Phát hiện quốc gia bằng AI: '{potential_country}'")

            if potential_country:
                context_to_return['country'] = potential_country
                logger.info(f"Quốc gia mới từ câu hỏi: {potential_country}")
                if potential_country.lower() not in self.visa_data:
                    await self.load_visa_data(potential_country)
            elif user_context and 'country' in user_context:
                context_to_return['country'] = user_context['country']

            if user_context and 'user_id' in user_context:
                from services.database import db
                users_collection = db.get_collection("users")
                users_collection.update_one(
                    {"user_id": user_context['user_id']},
                    {"$set": {"context": context_to_return}},
                    upsert=True
                )

            country = context_to_return.get('country') or (user_context.get('country') if user_context else None)
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
            
            # THAY ĐỔI Ở ĐÂY
            raw_response = await self._generate_response(prompt)
            
            # Xử lý phản hồi dài
            if len(raw_response) > 160:
                # Phản hồi quá dài, trả về một mảng
                response_parts = self._split_message(raw_response)
                return {"type": "multi_part", "messages": response_parts}, context_to_return
            else:
                # Phản hồi ngắn, trả về một chuỗi đơn như trước
                return raw_response, context_to_return

        except Exception as e:
            logger.error(f"Lỗi trong process_visa_query: {e}", exc_info=True)
            return (
                "Xin lỗi, có lỗi xảy ra. Vui lòng liên hệ hotline 1900 636563 để được hỗ trợ.",
                user_context or {}
            )

    async def _save_customer_contact(self, name, phone, country, user_id, context=None):
        """Save customer contact with a detailed description capturing special cases."""
        from services.database import db
        from services.lead_service import lead_service
        try:
            leads_collection = db.get_collection("leads")
            existing_lead = leads_collection.find_one({"phone": phone})
            if existing_lead:
                logger.info(f"Lead với SĐT {phone} đã tồn tại, không cập nhật")
                return True

            if not name and context:
                name = self._extract_customer_name_from_context(context, phone)

            previous_messages = context.get('previous_messages', []) if context else []
            user_queries = [msg['message'] for msg in previous_messages if msg.get('sender') == 'user']

            original_query = None
            for msg in user_queries:
                if len(msg) > 15 and not msg.startswith(('hi', 'hello', 'chào', 'xin chào')):
                    original_query = msg
                    break

            default_desc = f"Khách hàng để lại số {phone} để tư vấn visa"
            if country:
                default_desc += f" - Quan tâm visa {country}"

            combined_text = " ".join(user_queries).lower()
            special_concerns = False
            special_case_types = []
            case_details = {}

            # Kiểm tra visa bị từ chối
            rejection_match = None
            for pattern in [
                r"(?:đã|từng|bị)\s+(?:rớt|trượt|từ chối)\s+visa\s+(\d+)\s+(?:lần|lan)",
                r"(?:rớt|trượt|từ chối)\s+visa\s+(\d+)\s+(?:lần|lan)",
                r"(?:đã|từng|bị)\s+(?:rớt|trượt|từ chối)\s+(\d+)\s+(?:lần|lan)"
            ]:
                matches = re.findall(pattern, combined_text)
                if matches:
                    rejection_match = matches[0]
                    special_concerns = True
                    special_case_types.append("previous_rejection")
                    case_details["previous_rejection"] = (
                        f"⚠️ Từng bị từ chối visa {country if country else ''} {rejection_match} lần"
                    )
                    break

            # Kiểm tra người thân ở lại bất hợp pháp
            if any(term in combined_text for term in ['bất hợp pháp', 'người thân ở', 'người thân bên đó', 'ở lại']):
                special_concerns = True
                special_case_types.append("illegal_stay")
                case_details["illegal_stay"] = (
                    f"⚠️ Có người thân ở {country if country else 'nước ngoài'} bất hợp pháp"
                )

            # Kiểm tra không có sổ tiết kiệm
            if any(term in combined_text for term in ['không có sổ', 'không stk', 'ko stk', 'không tài khoản']):
                special_concerns = True
                special_case_types.append("no_savings")
                case_details["no_savings"] = "⚠️ Không có sổ tiết kiệm"

            # Kiểm tra công việc tự do
            if any(term in combined_text for term in ['tự do', 'freelance', 'không công ty', 'làm tự do']):
                special_concerns = True
                special_case_types.append("freelance_job")
                case_details["freelance_job"] = "⚠️ Làm việc tự do/freelance"

            # Xây dựng mô tả cuối cùng
            description_parts = []
            for case_type in special_case_types:
                description_parts.append(case_details[case_type])

            if country and not any("visa" in part.lower() and country.lower() in part.lower() for part in description_parts):
                description_parts.append(f"Quan tâm visa {country}")

            if name:
                description_parts.append(f"{name}: {phone}")
            else:
                description_parts.append(f"SĐT: {phone}")

            final_description = " - ".join(description_parts)
            if not description_parts:
                final_description = default_desc

            customer_data = {
                "name": name or "",
                "phone": phone,
                "country_interest": country or "chưa xác định",
                "zalo_user_id": user_id,
                "source": "zalo_bot",
                "status": "new_lead",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "original_query": original_query,
                "special_concerns": special_concerns,
                "special_case_types": special_case_types,
                "description": final_description
            }

            lead_id = lead_service.create_lead_with_description(customer_data, final_description)
            logger.info(f"Đã lưu thông tin khách hàng: {phone} với mô tả: {final_description}")
            return True

        except Exception as e:
            logger.error(f"Lỗi khi lưu thông tin khách hàng: {e}", exc_info=True)
            return False

    def _extract_customer_name_from_context(self, context, phone=None):
        """Extract customer name from context more thoroughly."""
        try:
            previous_messages = context.get('previous_messages', [])
            user_messages = [msg['message'] for msg in previous_messages if msg.get('sender') == 'user']

            if not user_messages:
                return None

            for message in user_messages:
                name = self._extract_customer_name(message)
                if name:
                    return name

            if phone:
                for message in user_messages:
                    if phone in message:
                        parts = message.split(phone)
                        if parts and parts[0].strip():
                            potential_name = parts[0].strip()
                            potential_name = re.sub(
                                r'^(sđt|số|tôi là|tên|là|gọi|chào|a|anh|chị|em|c|e|hello|hi|xin chào|xin)\s+',
                                '', potential_name, flags=re.IGNORECASE
                            )
                            potential_name = re.sub(r'[:,.;]+$', '', potential_name)
                            if potential_name and 2 <= len(potential_name) <= 30:
                                return potential_name

            if user_messages:
                last_message = user_messages[-1]
                if phone and phone in last_message:
                    for separator in ['-', ':', ' ', ',']:
                        parts = last_message.split(separator)
                        for i, part in enumerate(parts):
                            if phone in part:
                                if i > 0 and len(parts[i-1].strip()) > 1:
                                    return parts[i-1].strip()
                                elif i < len(parts)-1 and len(parts[i+1].strip()) > 1:
                                    return parts[i+1].strip()

            return None
        except Exception:
            return None

    def _extract_customer_name(self, text):
        """Extract customer name from text."""
        if not text:
            return None
        name_patterns = [
            r'(?:tên|tôi|mình|tui|em|anh|chị) (?:là|tên là|tên|gọi là) ([A-Za-zÀ-ỹ\s]{2,30})',
            r'(?:tên|họ tên|họ và tên)[:\s]+([A-Za-zÀ-ỹ\s]{2,30})',
            r'(\b[A-Za-zÀ-ỹ\s]{2,30}\b)(?=\s*(?:\d{9,11}|\+84\d{9,10}))'
        ]
        for pattern in name_patterns:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                return matches.group(1).strip()

        phone_pattern = r'(0[0-9]{9,10})|(\+84[0-9]{9,10})'
        phone_matches = re.findall(phone_pattern, text)
        if phone_matches:
            phone = None
            for match in phone_matches:
                for group in match:
                    if group:
                        phone = group
                        break
                if phone:
                    break
            if phone:
                parts = text.split(phone)
                if parts[0].strip():
                    potential_name = parts[0].strip()
                    potential_name = re.sub(
                        r'^(sđt|số|tôi là|tên|là|gọi|chào|a|anh|chị|em|c|e|hello|hi|xin chào|xin)\s+',
                        '', potential_name, flags=re.IGNORECASE
                    )
                    potential_name = re.sub(r'[:,.;]+$', '', potential_name)
                    if potential_name and 2 <= len(potential_name) <= 30:
                        return potential_name
                if len(parts) > 1 and parts[1].strip():
                    potential_name = parts[1].strip()
                    if potential_name and 2 <= len(potential_name) <= 30:
                        return potential_name
        return None
    

    def _extract_country_from_query(self, query):
        """Extract country from the user's query with more strict validation."""
        if not query:
            return None
            
        query_lower = query.lower()
        
        # Kiểm tra một cách nghiêm ngặt hơn với các từ khóa rõ ràng
        country_keywords = {
            "trung quốc": ["trung quoc", "china", "tq ", "trung hoa", "china"],
            "nhật bản": ["nhật", "japan", "nhat ban", "jp"],
            "hàn quốc": ["hàn", "korea", "han quoc", "south korea", "hq"],
            "đài loan": ["đài loan", "dai loan", "taiwan"],
            "hongkong": ["hong kong", "hồng kông", "hk"],
            "macau": ["ma cao", "macao"],
            "singapore": ["sing", "singapore"],
            "ấn độ": ["ấn độ", "an do", "india", "ấn độ"],
            "thái lan": ["thái", "thai lan", "thailand"],
            "malaysia": ["malay", "malaysia"],
            "indonesia": ["indo", "indon"],
            "philippines": ["philipin", "phi"],
            "việt nam": ["việt nam", "viet nam", "vn"],
            "pakistan": ["pak", "pakistan"],
            "myanmar": ["myan", "miến điện", "mien dien", "burma"],
            "triều tiên": ["trieu tien", "north korea"],
            "nga": ["nga ", "russia", "liên bang nga", "lien bang nga", "russian"],
            "đức": ["đức ", "duc ", "germany", "german", "đức quốc"],
            "pháp": ["pháp ", "phap ", "france", "french"],
            "ý": ["ý ", "y ", "italy", "italia", "italian"],
            "anh": ["anh quốc", "uk", "england", "british"],
            "tây ban nha": ["tbn", "tay ban nha", "spain", "spanish"],
            "bồ đào nha": ["bo dao nha", "portugal"],
            "hà lan": ["ha lan", "netherlands", "dutch"],
            "bỉ": ["bỉ ", "bi ", "belgium", "belgian"],
            "đan mạch": ["dan mach", "denmark", "danish"],
            "thụy điển": ["thuy dien", "sweden", "swedish"],
            "thụy sĩ": ["thuy si", "switzerland", "swiss"],
            "áo": ["áo ", "ao ", "austria", "austrian"],
            "hy lạp": ["hy lap", "greece", "greek"],
            "phần lan": ["phan lan", "finland", "finnish"],
            "na uy": ["na uy", "norway", "norwegian"],
            "ireland": ["ai len", "ái len", "ireland"],
            "ba lan": ["ba lan", "poland", "polish"],
            "cộng hòa séc": ["ch séc", "séc", "czech", "czechia"],
            "mỹ": ["mỹ ", "usa", "america", "united states", "my ", "hoa kỳ"],
            "canada": ["canada"],
            "mexico": ["mê hi cô", "me hi co", "mexico"],
            "brazil": ["bra-xin", "bra zin", "brazil"],
            "argentina": ["ác hen ti na", "ac hen ti na", "argentina"],
            "peru": ["pê ru", "pe ru", "peru"],
            "chile": ["chi lê", "chi le", "chile"],
            "colombia": ["cô lôm bi a", "co lom bia", "colombia"],
            "cuba": ["cu ba", "cuba"],
            "úc": ["úc ", "australia", "uc ", "au ", "nước úc"],
            "new zealand": ["nz", "niu di lân", "new zealand"],
            "nam phi": ["south africa", "nam phi"],
            "ai cập": ["ai cap", "egypt"],
            "maroc": ["ma rốc", "morocco", "maroc"],
            "kenya": ["kê ni a", "ke ni a", "kenya"],
            "namibia": ["na-mi-bi-a", "namibia"],
            "ả rập xê út": ["saudi arabia", "a rap xe ut", "saudi"],
            "qatar": ["catar", "ca ta", "qatar"],
            "thổ nhĩ kỳ": ["thổ", "tho nhi ky", "turkey", "turkish"],
            "dubai": ["du bai", "uae", "emirates"],
            "schengen": ["sen-gen", "khối schengen", "châu âu", "eu"],
            "trung đông": ["middle east", "trung đông"],
            "châu phi": ["africa", "châu phi"],
            "đông nam á": ["southeast asia", "asean", "đông nam á"]
        }
        
        # Xác minh chặt chẽ hơn cho từng quốc gia
        for country, keywords in country_keywords.items():
            for keyword in keywords:
                # Tìm kiếm chính xác từ khóa trong câu
                # Thêm dấu cách hoặc ranh giới từ để tránh kết quả sai
                if (f" {keyword} " in f" {query_lower} " or 
                    query_lower.startswith(f"{keyword} ") or 
                    query_lower.endswith(f" {keyword}") or
                    query_lower == keyword):
                    
                    # Xác thực thêm để loại trừ các từ đa nghĩa
                    if self._is_valid_country_detection(country, query):
                        return country
        
        # Nếu không tìm thấy quốc gia rõ ràng, trả về None
        return None

    def _is_valid_country_detection(self, detected_country, query):
        """Validate if a country detection is likely correct and not a false positive."""
        query_lower = query.lower()
        
        # Nếu query bắt đầu bằng "visa" hoặc "giá visa" và tiếp theo là tên quốc gia
        # thì xác định đây là hỏi về visa của quốc gia đó
        visa_patterns = [
            f"visa {detected_country.lower()}",
            f"giá visa {detected_country.lower()}",
            f"chi phí visa {detected_country.lower()}"
        ]
        
        if any(pattern in query_lower for pattern in visa_patterns):
            # Nếu query có dạng "visa <tên quốc gia>" hoặc "giá visa <tên quốc gia>"
            # thì ưu tiên xác định đây là query về quốc gia, bất kể từ "anh" có xuất hiện
            # trong các từ ambiguous không
            logger.info(f"Phát hiện hợp lệ: '{detected_country}' trong pattern '{[p for p in visa_patterns if p in query_lower]}'")
            return True
        
        # Giữ lại code hiện tại để kiểm tra các trường hợp khác...
        
        # Các từ có thể gây hiểu nhầm
        ambiguous_words = {
            "ý định", "ý nghĩa", "ý là", "ý ạ", "ý nhé", 
            "anh nhé", "anh ạ", "anh/chị", "anh chị", 
            "vì", "ý kiến", "tôi", "công ty", "cty", "mình"
        }
        
        # Kiểm tra các trường hợp dễ nhầm lẫn
        for phrase in ambiguous_words:
            if phrase in query_lower:
                # Nếu "ý" là quốc gia đang kiểm tra và từ "ý" trong từ đa nghĩa
                if detected_country == "ý" and "ý" in phrase:
                    return False
                # Nếu "anh" là quốc gia đang kiểm tra và từ "anh" trong từ đa nghĩa
                if detected_country == "anh" and "anh" in phrase:
                    return False
        
        # Kiểm tra thêm độ chắc chắn
        detection_patterns = {
            "ý": [r'\bý\b', r'\by\b', r'\bitaly\b', r'\bitalia\b'],
            "anh": [r'\banh quốc\b', r'\bengland\b', r'\buk\b', r'\bbritish\b'],
            "nga": [r'\bnga\b', r'\brussia\b', r'\bliên bang nga\b'],
            "đức": [r'\bđức\b', r'\bduc\b', r'\bgermany\b', r'\bgerman\b'],
            "mỹ": [r'\bmỹ\b', r'\bmy\b', r'\busa\b', r'\bamerica\b']
        }
        
        # Nếu quốc gia cần xác minh nghiêm ngặt hơn
        if detected_country in detection_patterns:
            patterns = detection_patterns[detected_country]
            return any(re.search(pattern, query_lower) for pattern in patterns)
        
        # Cho các quốc gia khác, chấp nhận phát hiện ban đầu
        return True

    def _extract_family_travel(self, query):
        """Detect if the user intends to travel with family."""
        query_lower = query.lower()
        family_keywords = [
            "gia đình", "vợ", "chồng", "con", "con trai", "con gái",
            "ba mẹ", "bố mẹ", "cha mẹ", "cả nhà"
        ]
        return any(keyword in query_lower for keyword in family_keywords)

    def _extract_stay_duration(self, query):
        """Extract intended stay duration from query."""
        query_lower = query.lower()
        duration_matches = re.findall(r'(\d+)\s*(ngày|tuần|tháng|năm|thang|nam|tuan)', query_lower)
        if duration_matches:
            number, unit = duration_matches[0]
            number = int(number)
            days = (
                number * (
                    30 if unit in ["tháng", "thang"] else
                    7 if unit in ["tuần", "tuan"] else
                    365 if unit in ["năm", "nam"] else 1
                )
            )
            return {"value": number, "unit": unit, "days": days}

        long_stay_keywords = ["lâu hơn", "dài hạn", "ở lâu", "nhiều ngày", "nhiều tháng"]
        if any(keyword in query_lower for keyword in long_stay_keywords):
            return {"long_stay": True}
        return None

    def _select_best_visa(self, country, context):
        """Select the most suitable visa based on context."""
        visas = self.visa_data.get(country, [])
        if not visas:
            return None

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
        logger.info(f"Selected visa for {country}: {best_visa.get('price')} USD")
        return best_visa

    def _convert_duration_to_days(self, duration_str):
        """Convert visa duration string to days."""
        if not duration_str:
            return 0
        duration_str = duration_str.lower()
        if "ngày" in duration_str:
            try:
                return int(re.search(r'(\d+)', duration_str).group(1))
            except Exception:
                return 30
        elif "tháng" in duration_str:
            try:
                months = int(re.search(r'(\d+)', duration_str).group(1))
                return months * 30
            except Exception:
                return 90
        elif "năm" in duration_str:
            try:
                years = int(re.search(r'(\d+)', duration_str).group(1))
                return years * 365
            except Exception:
                return 365
        return 90

    async def _generate_response(self, prompt):
        """Generate response using Gemini API."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: self.model.generate_content(prompt))
            result = response.text.strip()
            if len(result) < 100 and "số điện thoại" not in result.lower():
                result += " Anh/chị vui lòng để lại số điện thoại để tư vấn viên liên hệ hỗ trợ chi tiết nhé!"
            return result
        except Exception as e:
            logger.error(f"Lỗi khi tạo phản hồi: {e}")
            return "Xin lỗi, tôi không thể trả lời vào lúc này. Vui lòng gọi 1900 636563 để được hỗ trợ."

    def _build_visa_prompt(self, query, visa_info, context_str="", user_context=None):
        """Build an effective prompt for visa queries with optimized price range."""
        prompt = (
            "Bạn là tư vấn viên visa chuyên nghiệp tại Passport Lounge với giọng điệu tự nhiên giống người, lịch sự và thân thiện.\n"
            "CẢNH BÁO QUAN TRỌNG: Phản hồi của bạn PHẢI NGẮN GỌN (tối đa 4-5 câu, khoảng 300-400 ký tự).\n"
            "KHÔNG liệt kê chi tiết giấy tờ hay quy trình cụ thể.\n"
            "Giọng điệu thân thiện, đồng cảm và tự nhiên.\n"
            "Khi nói về giá, LUÔN sử dụng khoảng giá hợp lý (ví dụ: 'khoảng 7-8 triệu') thay vì số chính xác.\n"
        )
        if context_str:
            prompt += f"\nNgữ cảnh cuộc hội thoại:\n{context_str}\n"

        if visa_info:
            country_name = visa_info.get('country', '').lower()
            prompt += f"\nDữ liệu sản phẩm visa {country_name}:\n"
            prompt += f"- Loại visa: {visa_info.get('visa_type', '')} {visa_info.get('visa_method', '')}\n"
            
            # Tính toán giá với range hợp lý
            price = visa_info.get('price', 0)
            if price:
                price_vnd = int(price * 25000)  # Tỷ giá 25,000 VND/USD
                price_million = price_vnd / 1000000  # Quy đổi sang triệu VND

                # Phân loại quốc gia và tính range giá hợp lý
                premium_countries = ['mỹ', 'anh quốc', 'canada', 'úc', 'new zealand']
                schengen_countries = ['đức (visa schengen)', 'ý (visa schengen)', 'pháp (visa schengen)', 
                                    'tây ban nha (visa schengen)', 'thụy sĩ (visa schengen)', 
                                    'thụy điển (visa schengen)', 'ch séc (visa schengen)', 
                                    'phần lan (visa schengen)', 'na uy (visa schengen)', 
                                    'hy lạp (visa schengen)', 'hà lan (visa schengen)', 
                                    'đan mạch (visa schengen)', 'bồ đào nha (visa schengen)', 
                                    'bỉ (visa schengen)', 'áo (visa schengen)']

                if country_name in premium_countries:
                    # Nhóm cao cấp: range ±15% (không quá rộng, hợp lý)
                    price_range_low = round(price_million * 0.85, 1)
                    price_range_high = round(price_million * 1.15, 1)
                elif country_name in schengen_countries:
                    # Nhóm Schengen: range ±10% (hẹp hơn vì giá đồng nhất)
                    price_range_low = round(price_million * 0.9, 1)
                    price_range_high = round(price_million * 1.1, 1)
                else:
                    # Nhóm khác: range ±12% (trung bình, tối ưu)
                    price_range_low = round(price_million * 0.88, 1)
                    price_range_high = round(price_million * 1.12, 1)

                # Điều chỉnh để range không quá rộng (tối đa chênh 2 triệu)
                if price_range_high - price_range_low > 2:
                    price_range_high = price_range_low + 2

                # Đảm bảo range hợp lý (ít nhất chênh 0.5 triệu)
                if price_range_high - price_range_low < 0.5:
                    price_range_high = price_range_low + 0.5

                prompt += f"- Giá thật: ${price} USD (khoảng {price_vnd:,} VND)\n"
                prompt += f"- Giá báo khách: khoảng {price_range_low}-{price_range_high} triệu VND\n"
            
            prompt += f"- Thời gian xử lý: {visa_info.get('processing_time', '')}\n"
        else:
            prompt += (
                "\nKhông có dữ liệu cụ thể về visa này trong cơ sở dữ liệu. "
                "Trả lời ngắn gọn và hỏi thêm thông tin để hiểu nhu cầu khách hàng."
            )

        has_concerns = user_context and user_context.get('has_special_concerns', False)
        if has_concerns:
            prompt += (
                "\nKhách hàng đang lo lắng về một số điều kiện đặc biệt. Khi trả lời:\n"
                "1. Thể hiện sự đồng cảm và sự tự tin giải quyết.\n"
                "2. Đề cập rằng Passport Lounge có giải pháp cho trường hợp đặc biệt này.\n"
                "3. Nói đã giúp nhiều khách hàng tương tự thành công.\n"
                "4. ĐỀ CẬP RẰNG: Để tư vấn chi tiết cho trường hợp này, cần liên hệ hotline 1900 636563 hoặc để lại SĐT.\n"
            )

        prompt += f"\nCâu hỏi hiện tại: {query}\n"
        prompt += (
            "\nHƯỚNG DẪN PHẢN HỒI:\n"
            "- Trả lời với độ dài vừa đủ (4-5 câu ngắn) để cung cấp thông tin hữu ích.\n"
            "- Thể hiện sự hiểu biết chuyên sâu và đồng cảm với khách hàng.\n"
            "- Trả lời cụ thể nhưng không đi vào chi tiết kỹ thuật.\n"
            "- Khi được hỏi về giá, LUÔN đưa ra khoảng giá hợp lý dựa trên dữ liệu.\n"
            "- THƯỜNG XUYÊN KẾT THÚC các câu trả lời bằng câu hỏi đơn giản như "
            "'Anh/chị còn thắc mắc gì nữa không?' hoặc 'Anh/chị quan tâm đến điều gì khác không?'\n"
            "\nHƯỚNG DẪN VỀ LIÊN HỆ:\n"
            "- Trường hợp khách cần hỗ trợ phức tạp hoặc quan tâm đến giá/chi tiết dịch vụ, "
            "khuyến khích để lại SĐT hoặc gọi hotline: "
            "'Anh/chị có thể để lại SĐT hoặc gọi 1900 636563 để được hỗ trợ tốt nhất.'\n"
            "- Trường hợp khách hỏi về hồ sơ phức tạp, tài chính, công việc: "
            "đề cập hotline 1900 636563 hoặc gợi ý để lại SĐT.\n"
            "- Đề xuất liên hệ một cách tự nhiên, không gây áp lực, chẳng hạn "
            "'Để tư vấn chi tiết hơn, anh/chị có thể để lại SĐT hoặc gọi hotline 1900 636563 ạ'.\n"
        )
        return prompt

    def _extract_phone_number(self, text):
        """Extract phone number from text."""
        if not text:
            return None
        phone_pattern = r'(0[0-9]{9,10})|(\+84[0-9]{9,10})'
        matches = re.findall(phone_pattern, text)
        if matches:
            for match in matches:
                for group in match:
                    if group:
                        return group
        return None

    def _detect_customer_concerns(self, query):
        """Detect special concerns from the customer's query."""
        query = query.lower()
        special_concern_patterns = [
            # Financial concerns
            "không có sổ tiết kiệm", "ko có sổ", "chưa có sổ", "không đủ tiền",
            "không chứng minh được tài chính", "không đủ tài chính",
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
            "bị trượt visa", "đã trượt", "bị đánh trượt", "từng bị trượt", "rớt",
            # Quick processing concerns
            "cần gấp", "khẩn", "nhanh", "sớm", "tuần sau", "vài ngày tới",
            "cuối tháng", "gấp rút", "express", "cấp tốc"
        ]
        return any(pattern in query for pattern in special_concern_patterns)

    async def _extract_country_with_ai(self, query):
        """Sử dụng AI để nhận diện quốc gia từ câu hỏi với cải tiến xử lý tin nhắn."""
        if not query:
            return None
        
        # Phát hiện quốc gia bằng pattern trước (nhanh hơn)
        country_from_pattern = self._extract_country_from_query(query)
        if country_from_pattern:
            logger.info(f"Phát hiện quốc gia từ pattern: '{country_from_pattern}'")
            return country_from_pattern
        
        # Nếu không tìm được bằng pattern, sử dụng AI
        prompt = (
            "Nhiệm vụ: Xác định quốc gia được đề cập trong câu hỏi về visa dưới đây.\n"
            "Nếu có quốc gia, trả về TÊN QUỐC GIA chính xác (tiếng Việt). "
            "Nếu không có quốc gia nào được đề cập, trả về NONE.\n\n"
            f"Câu hỏi: {query}\n\n"
            "Chỉ trả lời TÊN QUỐC GIA hoặc NONE, không có giải thích thêm.\n\n"
            "LƯU Ý ĐẶC BIỆT: Từ 'anh', 'ý' có thể là quốc gia hoặc từ khác tùy ngữ cảnh.\n"
            "- Nếu 'anh' là đại từ nhân xưng (anh ấy, anh trai...) -> NONE\n"
            "- Nếu 'anh' là quốc gia (visa anh, đi anh...) -> 'anh quốc'\n"
            "- Nếu 'ý' là danh từ (ý kiến, ý định...) -> NONE\n"
            "- Nếu 'ý' là quốc gia (visa ý, đi ý...) -> 'ý'\n\n"
            "Ví dụ:\n"
            "Câu: 'Tôi muốn làm visa đi Pháp' → 'pháp'\n"
            "Câu: 'Giá visa Mỹ bao nhiêu?' → 'mỹ'\n"
            "Câu: 'Anh có thể tư vấn về visa không?' → 'NONE'\n"
            "Câu: 'Tôi muốn visa Anh' → 'anh quốc'\n"
            "Câu: 'Tôi có ý định xin visa Ý' → 'ý'\n"
        )
        
        try:
            # Gửi prompt tới Gemini API
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: self.model.generate_content(prompt))
            result = response.text.strip().lower()
            
            # Loại bỏ dấu câu và ký tự thừa
            result = re.sub(r'[.,;:"\']', '', result)
            
            # Xử lý phản hồi
            logger.info(f"AI nhận diện quốc gia từ '{query}': '{result}'")
            
            if result == "none" or not result:
                return None
                
            # Chuẩn hóa tên quốc gia
            return self._standardize_country_name(result)
            
        except Exception as e:
            logger.error(f"Lỗi khi sử dụng AI để nhận diện quốc gia: {e}")
            return None

    def _standardize_country_name(self, country_name):
        """Chuẩn hóa tên quốc gia."""
        # Ánh xạ tên quốc gia cơ bản
        country_mapping = {
            "mỹ": "mỹ", "usa": "mỹ", "hoa kỳ": "mỹ",
            "anh": "anh quốc", "england": "anh quốc", "uk": "anh quốc", "vương quốc anh": "anh quốc",
            "nhật": "nhật bản", "japan": "nhật bản",
            "hàn": "hàn quốc", "hàn quốc": "hàn quốc", "korea": "hàn quốc",
            "úc": "úc", "australia": "úc"
        }
        
        country_name = country_name.lower().strip()
        return country_mapping.get(country_name, country_name)

    def _split_message(self, message):
        """Chia nhỏ tin nhắn nếu vượt quá giới hạn ký tự của Zalo."""
        ZALO_MESSAGE_LIMIT = 160  # Giới hạn ký tự Zalo
        
        if len(message) <= ZALO_MESSAGE_LIMIT:
            return [message]
        
        messages = []
        lines = message.split('\n')
        current_message = ""
        
        for line in lines:
            if len(current_message) + len(line) + 1 > ZALO_MESSAGE_LIMIT:
                if current_message:
                    messages.append(current_message.strip())
                current_message = line
            else:
                current_message += f"\n{line}" if current_message else line
        
        if current_message:
            messages.append(current_message.strip())
        
        return messages

    async def _generate_and_format_response(self, prompt, context):
        """Tạo phản hồi và định dạng phù hợp."""
        raw_response = await self._generate_response(prompt)
        
        # Thêm tag quốc gia nếu có
        if context.get('country'):
            country = context.get('country')
            if not re.search(rf'\b{re.escape(country)}\b', raw_response, re.IGNORECASE):
                # Thêm tên quốc gia vào đầu câu trả lời nếu chưa có
                raw_response = f"Về visa {country}, {raw_response[0].lower()}{raw_response[1:]}"
        
        # Thêm tagline dịch vụ nếu phản hồi quá ngắn
        if len(raw_response) < 100 and "số điện thoại" not in raw_response.lower():
            raw_response += " Anh/chị vui lòng để lại số điện thoại để tư vấn viên liên hệ hỗ trợ chi tiết nhé!"
        
        return raw_response, context

    def _is_country_reference(self, query, word):
        """Xác định chắc chắn từ 'anh' hoặc 'ý' là quốc gia."""
        query_lower = query.lower()
        
        # Các pattern chỉ rõ là quốc gia
        country_patterns = [
            rf"visa\s+{word}",
            rf"đi\s+{word}",
            rf"{word}\s+quốc",
            rf"du lịch\s+{word}",
            rf"phí\s+{word}",
            rf"giá\s+visa\s+{word}"
        ]
        
        # Nếu match bất kỳ pattern nào, đó là quốc gia
        for pattern in country_patterns:
            if re.search(pattern, query_lower):
                return True
        
        # Các pattern chỉ rõ KHÔNG phải quốc gia
        if word == "anh":
            non_country_patterns = [
                r"anh\s+chị", r"của\s+anh", r"anh\s+có", r"anh\s+ơi", 
                r"anh\s+nhé", r"anh\s+ạ", r"anh\s+[a-zà-ỹ]+"
            ]
        else:  # word == "ý"
            non_country_patterns = [
                r"ý\s+kiến", r"ý\s+định", r"ý\s+nghĩa", r"ý\s+là", 
                r"có\s+ý", r"theo\s+ý", r"ý\s+tưởng"
            ]
        
        # Nếu match bất kỳ pattern phi quốc gia, chắc chắn không phải quốc gia
        for pattern in non_country_patterns:
            if re.search(pattern, query_lower):
                return False
        
        # Kiểm tra ngữ cảnh từ
        words = query_lower.split()
        if word in words:
            idx = words.index(word)
            # Từ đứng ngay sau visa có khả năng cao là quốc gia
            if idx > 0 and words[idx-1] == "visa":
                return True
        
        # Mặc định: không chắc chắn
        return None

ai_processor = AIProcessor()