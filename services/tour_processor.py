#!/usr/bin/env python3
"""
AI Processor for private tour pricing and consultation with optimized logic and persistent context.
Base price is per person per day.
"""
import asyncio
import json
import logging
import re
from datetime import datetime

import google.generativeai as genai
import redis
from config import Config  # Assumes Config contains API key

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Redis for persistent storage
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Giới hạn ký tự tối đa cho một tin nhắn Zalo (160 ký tự)
ZALO_MESSAGE_LIMIT = 160

class TourPriceProcessor:
    def __init__(self):
        """Khởi tạo processor với cấu hình AI và dữ liệu giá tour."""
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.tour_pricing = self._load_tour_pricing_data()

    def _load_tour_pricing_data(self):
        """Tải dữ liệu giá tour được cấu hình với các khu vực và mức giá (giá/người/ngày)."""
        return {
            "asia_high": ["nhật bản|nhật|japan", "hàn quốc|hàn|korea"],
            "asia_low": ["đông nam á|thái lan|thailand|singapore|malaysia|indonesia|việt nam|philippines|campuchia|lào|myanmar|ấn độ|sri lanka"],
            "west_europe_oceania": ["tây âu|pháp|italy|đức|hà lan|spain|bồ đào nha|thụy sĩ|áo|paris|úc|australia|new zealand|nz|oceania"],
            "east_europe_middle_east": ["đông âu|thổ nhĩ kỳ|ai cập"],
            "uk": ["uk|anh"],
            "america": ["mỹ|usa|hawaii|los angeles|new york|las vegas|san francisco|canada"],
            "middle_east_africa_mongolia": ["trung đông|châu phi|mông cổ"],
            "taiwan_hk_russia": ["đài loan|hong kong|nga"],
            "pricing": {
                "asia_high": [
                    {"pax": (3, 4), "base_price_short": 400.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -40.00, "guide_fee": 150.00, "long_days": 8, "note": "Tài xế kiêm HDV"},
                    {"pax": (5, 6), "base_price_short": 360.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -40.00, "guide_fee": 150.00, "long_days": 8, "note": "Tài xế + HDV"},
                    {"pax": (7, 10), "base_price_short": 320.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -40.00, "guide_fee": 150.00, "long_days": 8, "note": "Tài xế + HDV"},
                    {"pax": (11, 16), "base_price_short": 280.00, "long_price_discount_percentage": 3.0, "no_meal_discount": -40.00, "guide_fee": 150.00, "long_days": 8, "note": "Tài xế + HDV"}
                ],
                "asia_low": [
                    {"pax": (3, 4), "base_price_short": 300.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -35.00, "guide_fee": 100.00, "long_days": 10, "note": "Tài xế + HDV"},
                    {"pax": (5, 6), "base_price_short": 260.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -35.00, "guide_fee": 110.00, "long_days": 10, "note": "Tài xế + HDV"},
                    {"pax": (7, 10), "base_price_short": 220.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -30.00, "guide_fee": 120.00, "long_days": 10, "note": "Tài xế + HDV"},
                    {"pax": (11, 16), "base_price_short": 200.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -30.00, "guide_fee": 140.00, "long_days": 10, "note": "Tài xế + HDV"}
                ],
                "west_europe_oceania": [
                    {"pax": (3, 4), "base_price_short": 450.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -60.00, "guide_fee": 200.00, "long_days": 10, "note": "Tài xế kiêm HDV"},
                    {"pax": (5, 6), "base_price_short": 430.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -60.00, "guide_fee": 200.00, "long_days": 10, "note": "Tài xế kiêm HDV"},
                    {"pax": (7, 10), "base_price_short": 400.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -55.00, "guide_fee": 220.00, "long_days": 10, "note": "Tài xế + HDV"},
                    {"pax": (11, 16), "base_price_short": 380.00, "long_price_discount_percentage": 3.0, "no_meal_discount": -55.00, "guide_fee": 240.00, "long_days": 10, "note": "Tài xế + HDV"}
                ],
                "east_europe_middle_east": [
                    {"pax": (3, 4), "base_price_short": 400.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -50.00, "guide_fee": 150.00, "long_days": 10, "note": "Tài xế + HDV"},
                    {"pax": (5, 6), "base_price_short": 360.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -50.00, "guide_fee": 160.00, "long_days": 10, "note": "Tài xế + HDV"},
                    {"pax": (7, 10), "base_price_short": 320.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -45.00, "guide_fee": 180.00, "long_days": 10, "note": "Tài xế + HDV"},
                    {"pax": (11, 16), "base_price_short": 300.00, "long_price_discount_percentage": 3.0, "no_meal_discount": -45.00, "guide_fee": 200.00, "long_days": 10, "note": "Tài xế + HDV"}
                ],
                "uk": [
                    {"pax": (3, 4), "base_price_short": 500.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -80.00, "guide_fee": 300.00, "long_days": 10, "note": "Tài xế kiêm HDV"},
                    {"pax": (5, 6), "base_price_short": 480.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -80.00, "guide_fee": 300.00, "long_days": 10, "note": "Tài xế kiêm HDV"},
                    {"pax": (7, 10), "base_price_short": 440.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -70.00, "guide_fee": 320.00, "long_days": 10, "note": "Tài xế + HDV"},
                    {"pax": (11, 16), "base_price_short": 400.00, "long_price_discount_percentage": 3.0, "no_meal_discount": -70.00, "guide_fee": 340.00, "long_days": 10, "note": "Tài xế + HDV"}
                ],
                "america": [
                    {"pax": (3, 4), "base_price_short": 480.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -80.00, "guide_fee": 300.00, "long_days": 10, "note": "Tài xế kiêm HDV"},
                    {"pax": (5, 6), "base_price_short": 460.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -80.00, "guide_fee": 300.00, "long_days": 10, "note": "Tài xế kiêm HDV"},
                    {"pax": (7, 10), "base_price_short": 420.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -70.00, "guide_fee": 320.00, "long_days": 10, "note": "Tài xế + HDV"},
                    {"pax": (11, 16), "base_price_short": 380.00, "long_price_discount_percentage": 3.0, "no_meal_discount": -60.00, "guide_fee": 340.00, "long_days": 10, "note": "Tài xế + HDV"}
                ],
                "middle_east_africa_mongolia": [
                    {"pax": (3, 4), "base_price_short": 440.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -50.00, "guide_fee": 200.00, "long_days": 10, "note": "Tài xế + HDV"},
                    {"pax": (5, 6), "base_price_short": 400.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -50.00, "guide_fee": 200.00, "long_days": 10, "note": "Tài xế + HDV"},
                    {"pax": (7, 10), "base_price_short": 340.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -45.00, "guide_fee": 220.00, "long_days": 10, "note": "Tài xế + HDV"},
                    {"pax": (11, 16), "base_price_short": 320.00, "long_price_discount_percentage": 3.0, "no_meal_discount": -45.00, "guide_fee": 240.00, "long_days": 10, "note": "Tài xế + HDV"}
                ],
                "taiwan_hk_russia": [
                    {"pax": (3, 4), "base_price_short": 350.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -40.00, "guide_fee": 150.00, "long_days": 10, "note": "Tài xế + HDV"},
                    {"pax": (5, 6), "base_price_short": 330.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -40.00, "guide_fee": 160.00, "long_days": 10, "note": "Tài xế + HDV"},
                    {"pax": (7, 10), "base_price_short": 280.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -35.00, "guide_fee": 180.00, "long_days": 10, "note": "Tài xế + HDV"},
                    {"pax": (11, 16), "base_price_short": 260.00, "long_price_discount_percentage": 3.0, "no_meal_discount": -35.00, "guide_fee": 200.00, "long_days": 10, "note": "Tài xế + HDV"}
                ]
            },
            "default_services": [
                "Visa du lịch",
                "HDV đón đoàn ở sân bay điểm đến, theo đoàn suốt hành trình",
                "Xe riêng có tài xế đưa đón sân bay và tham quan",
                "Vé tàu cao tốc hoặc máy bay nội địa (nếu có trong lịch trình)",
                "Khách sạn 3-4* hoặc căn hộ tương đương",
                "Ăn sáng tại khách sạn/căn hộ và 2 bữa chính",
                "Vé tham quan theo lịch trình",
                "Vé vui chơi, trải nghiệm theo lịch trình",
                "Bảo hiểm du lịch (bồi thường tối đa 50.000 USD)",
                "eSIM 1GB/ngày",
                "Ưu tiên làm thủ tục sân bay ở Tân Sơn Nhất",
                "Clip ký sự chuyến đi 5-10 phút"
            ]
        }

    def _get_region_from_country(self, country):
        """Xác định khu vực dựa trên quốc gia."""
        if not country:
            return "asia_high"
        country = country.lower().strip()
        for region, countries in self.tour_pricing.items():
            if region in ["pricing", "default_services"]:
                continue
            for country_group in countries:
                if any(keyword in country for keyword in country_group.split('|')):
                    return region
        return "asia_high"

    async def _analyze_conversation(self, user_query, user_id):
        """Phân tích hội thoại tour bằng AI."""
        try:
            context_key = f"context:{user_id}"
            history_key = f"history:{user_id}"
            current_context = json.loads(redis_client.get(context_key) or '{}')
            history = json.loads(redis_client.get(history_key) or '[]')[-10:]  # Tăng số lượng tin nhắn lịch sử

            # Định dạng lịch sử để AI dễ đọc
            history_formatted = ""
            for msg in history:
                if msg.startswith("User:"):
                    history_formatted += f"Khách: {msg[5:].strip()}\n"
                elif msg.startswith("Bot:"):
                    history_formatted += f"Bot: {msg[4:].strip()}\n"

            # Prompt AI cải tiến với ngữ cảnh đầy đủ
            prompt = (
                "Bạn là trợ lý AI phân tích hội thoại về tour du lịch và visa bằng tiếng Việt.\n\n"
                
                f"**Lịch sử hội thoại:**\n{history_formatted}\n\n"
                f"**Thông tin đã thu thập:**\n{json.dumps(current_context, ensure_ascii=False)}\n\n"
                f"**Tin nhắn hiện tại:**\n{user_query}\n\n"
                
                "**Nhiệm vụ của bạn:**\n"
                "1. GIỮ và TÍCH HỢP thông tin đã biết (locations, country, pax, days).\n"
                "2. Với câu trả lời ngắn như \"1 tuần\", \"5 người\", \"Nhật\" -> kết hợp với ngữ cảnh trước đó.\n"
                "3. Khi đủ thông tin (country hoặc locations, days, pax) -> đề xuất trả về ước tính giá ngay.\n"
                "4. Nhận diện nếu khách đang cần tư vấn visa hay tour.\n\n"
                
                "**Cần trả về JSON với cấu trúc sau:**\n"
                "{\n"
                "  \"context\": {\n"
                "    \"locations\": [list các địa điểm], // Ví dụ: [\"Tokyo\", \"Osaka\"]\n"
                "    \"country\": string, // Ví dụ: \"nhật bản\", \"hàn quốc\" (không dấu)\n"
                "    \"days\": number, // Ví dụ: 7 (cho \"1 tuần\")\n"
                "    \"pax\": number, // Số người đi tour\n"
                "    \"no_meal\": boolean, // Khách không cần bữa ăn\n"
                "    \"upgrade_hotel\": boolean, // Khách muốn nâng cấp khách sạn\n"
                "    \"phone\": string, // Số điện thoại (nếu có)\n"
                "    \"reset\": boolean, // Khách muốn reset hội thoại\n"
                "    \"service_type\": string // \"tour\" hoặc \"visa\" dựa trên nhu cầu\n"
                "  },\n"
                "  \"intent\": {\n"
                "    \"request_price\": boolean, // Khách yêu cầu báo giá, BẬT khi đủ thông tin\n"
                "    \"consultation\": boolean, // Khách muốn tư vấn\n"
                "    \"confirmation\": boolean // Khách đang xác nhận thông tin\n"
                "  },\n"
                "  \"ready_for_price\": boolean, // BẬT khi đã có country, days, pax\n"
                "  \"response\": string, // Gợi ý câu trả lời phù hợp\n"
                "  \"need_phone\": boolean // BẬT khi cần số điện thoại để tư vấn chi tiết\n"
                "}\n\n"
            )
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Xử lý kết quả
            result = json.loads(response_text.replace("```json", "").replace("```", ""))
            
            # Cập nhật context từ kết quả AI
            for key, value in result.get("context", {}).items():
                if value is not None:
                    current_context[key] = value

            # Xử lý các yêu cầu đặc biệt về lịch trình, nâng cấp dịch vụ, hoặc phản hồi đồng ý
            detailed_itinerary_keywords = ["lịch trình chi tiết", "chi tiết từng ngày", "lịch trình cụ thể", "có", "cần", "muốn", "đồng ý", "ok", "được"]
            upgrade_keywords = ["nâng cấp", "khách sạn", "vé máy bay", "phòng", "5 sao", "4 sao"]
            
            if any(keyword in user_query.lower() for keyword in detailed_itinerary_keywords):
                # Phát hiện yêu cầu lịch trình chi tiết hoặc phản hồi đồng ý
                country = current_context.get("country", "")
                days = current_context.get("days", "")
                contact_message = (
                    f"Dạ, với tour {country} {days} ngày, em có thể chia sẻ lịch trình chi tiết từng ngày đã được chuyên gia du lịch thiết kế. "
                    f"Anh/chị vui lòng để lại tên và số điện thoại hoặc gọi hotline 1900 636563, nhân viên tư vấn sẽ gửi chi tiết lịch trình và tư vấn cụ thể theo nhu cầu của gia đình mình ạ!"
                )
                return {
                    "context": current_context,
                    "intent": {"request_price": False, "consultation": True, "confirmation": True},
                    "ready_for_price": False,
                    "response": contact_message,
                    "need_contact": True
                }
            elif any(keyword in user_query.lower() for keyword in upgrade_keywords):
                # Phát hiện yêu cầu nâng cấp dịch vụ
                service_message = (
                    f"Dạ, để nâng cấp dịch vụ cho tour, chúng tôi có nhiều lựa chọn phù hợp với nhu cầu của gia đình anh/chị. "
                    f"Anh/chị vui lòng để lại tên và số điện thoại hoặc gọi hotline 1900 636563, nhân viên tư vấn sẽ liên hệ ngay với các gói dịch vụ nâng cấp tốt nhất ạ!"
                )
                return {
                    "context": current_context,
                    "intent": {"request_price": False, "consultation": True, "confirmation": False},
                    "ready_for_price": False,
                    "response": service_message,
                    "need_contact": True
                }
            
            # Cập nhật trạng thái vào Redis
            redis_client.set(context_key, json.dumps(current_context))
            
            # Thêm tin nhắn khách vào lịch sử
            history.append(f"User: {user_query}")
            redis_client.set(history_key, json.dumps(history[-10:]))  # Giữ 10 tin nhắn gần nhất
            
            return result
            
        except Exception as e:
            logger.error(f"Error in _analyze_conversation: {e}")
            return {
                "context": current_context,
                "intent": {"request_price": False, "consultation": True, "confirmation": False},
                "ready_for_price": False,
                "response": "Dạ, em chưa hiểu rõ yêu cầu. Anh/chị vui lòng cung cấp thêm thông tin nhé!"
            }

    def _split_message(self, message):
        """Chia nhỏ tin nhắn nếu vượt quá giới hạn ký tự của Zalo."""
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

    async def process_tour_query(self, user_id, user_query):
        """Xử lý truy vấn của người dùng và trả về danh sách phản hồi cùng context mới."""
        try:
            analysis = await self._analyze_conversation(user_query, user_id)
            # Lấy context từ Redis, nếu không có thì khởi tạo rỗng
            context = json.loads(redis_client.get(f"context:{user_id}") or '{}')
            
            # Cập nhật context từ analysis
            for key, value in analysis.get("context", {}).items():
                if value is not None:
                    context[key] = value
                    
            redis_client.set(f"context:{user_id}", json.dumps(context))
            
            # Xử lý reset
            if context.get("reset"):
                new_context = {"country": None, "days": None, "pax": None, "no_meal": False, "phone": None, "reset": False}
                redis_client.set(f"context:{user_id}", json.dumps(new_context))
                redis_client.delete(f"history:{user_id}")
                return ["Đã reset. Anh/chị có thể hỏi lại từ đầu nhé!"], new_context
                    
            # Xử lý số điện thoại
            if phone := context.get("phone"):
                self._save_customer_lead(user_id, context)
                return [f"Dạ, em đã ghi nhận SĐT {phone}. Nhân viên sẽ liên hệ sớm ạ!"], context
            
            # Kiểm tra nếu phân tích AI xác định cần lấy thông tin liên hệ
            if analysis.get("need_contact", False):
                # Cập nhật context để bot nhớ đang chờ thông tin liên hệ
                context["waiting_for_contact"] = True
                redis_client.set(f"context:{user_id}", json.dumps(context))
                
                response = analysis.get("response", "Dạ, anh/chị vui lòng để lại tên và số điện thoại để nhân viên tư vấn liên hệ ngay ạ!")
                messages = self._split_message(response)
                redis_client.set(f"history:{user_id}", json.dumps(
                    json.loads(redis_client.get(f"history:{user_id}") or '[]')[-4:] + [f"Bot: {response}"]
                ))
                return messages, context
                
            # Phone pattern detection - nếu phát hiện số điện thoại trong tin nhắn
            phone_pattern = r'(0[0-9]{9,10})|(\+84[0-9]{9,10})'
            phone_matches = re.findall(phone_pattern, user_query)
            if phone_matches and context.get("waiting_for_contact", False):
                phone_number = phone_matches[0][0] or phone_matches[0][1]
                context["phone"] = phone_number
                context["waiting_for_contact"] = False
                self._save_customer_lead(user_id, context)
                return [f"Cảm ơn anh/chị đã để lại số {phone_number}. Nhân viên tư vấn sẽ liên hệ ngay để gửi lịch trình chi tiết và tư vấn cụ thể ạ!"], context
                    
            # Tính giá khi đủ thông tin
            if analysis["ready_for_price"] and context.get("country") and context.get("pax") and context.get("days"):
                price_info = self._calculate_tour_price(
                    context["country"],
                    context["pax"],
                    context["days"],
                    context.get("no_meal", False)  # Mặc định False nếu không có trong context
                )
                response = self._build_price_response(price_info, context)
                messages = self._split_message(response)
                redis_client.set(f"history:{user_id}", json.dumps(
                    json.loads(redis_client.get(f"history:{user_id}") or '[]')[-4:] + [f"Bot: {response}"]
                ))
                return messages, context
                
            response = analysis.get("response", "Dạ, em cần thêm thông tin về địa điểm, số người hoặc số ngày để tư vấn chính xác hơn. Anh/chị vui lòng cung cấp thêm nhé!")
            messages = self._split_message(response)
            return messages, context
                
        except Exception as e:
            logger.error(f"Error in process_tour_query: {e}")
            return ["Dạ, hệ thống gặp lỗi nhỏ. Anh/chị thử lại nhé!"], json.loads(redis_client.get(f"context:{user_id}") or '{}')

    def _calculate_tour_price(self, country, pax, days, no_meal):
        """Tính toán giá tour dựa trên giá cơ bản 1 người/ngày, không cộng phí HDV riêng."""
        region = self._get_region_from_country(country)
        pricing = self.tour_pricing["pricing"].get(region, self.tour_pricing["pricing"]["asia_high"])
        
        tier = next((t for t in pricing if t["pax"][0] <= pax <= t["pax"][1]), pricing[-1])
        base_price_per_day = tier["base_price_short"]  # Giá cơ bản 1 người/ngày, đã bao gồm HDV

        # Tính giá mỗi ngày sau khi áp dụng giảm giá dài ngày (nếu có)
        if days >= tier["long_days"]:
            discount = tier["long_price_discount_percentage"] / 100
            base_price_per_day *= (1 - discount)

        # Áp dụng giảm giá không ăn (nếu có) trên giá mỗi ngày
        total_price_per_day_per_pax = base_price_per_day + (tier["no_meal_discount"] if no_meal else 0)
        
        # Tổng giá = giá/ngày/người * số ngày * số người (không cộng guide_fee)
        total_price = total_price_per_day_per_pax * days * pax
        total_price_per_pax = total_price_per_day_per_pax * days  # Tổng giá cho 1 người cả chuyến

        return {
            "total_price": total_price,
            "total_price_per_pax": total_price_per_pax,
            "days": days,
            "pax": pax,
            "region": region
        }

    def _save_customer_lead(self, user_id, context):
        """Lưu thông tin khách hàng tiềm năng vào cơ sở dữ liệu."""
        try:
            from services.database import db
            lead_data = {
                "phone": context["phone"],
                "zalo_user_id": user_id,
                "source": "zalo_bot",
                "created_at": datetime.now().isoformat(),
                "service_type": "tour",
                "country_interest": context.get("country", ""),
                "description": f"{context.get('country', '')}, {context.get('days', 'chưa xác định')} ngày, {context.get('pax', 'chưa xác định')} người"
            }
            db.get_collection("leads").insert_one(lead_data)
            logger.info(f"Đã lưu lead: {context['phone']}")
        except Exception as e:
            logger.error(f"Error saving lead: {e}")

    def _build_price_response(self, price_info, context):
        """Tạo phản hồi giá tour chi tiết với thông điệp linh hoạt."""
        total_usd = round(price_info["total_price"])
        per_pax_usd = round(price_info["total_price_per_pax"])
        services = self.tour_pricing["default_services"].copy()
        if context.get("no_meal"):
            services[services.index("Ăn sáng tại khách sạn/căn hộ và 2 bữa chính")] = "Ăn sáng tại khách sạn/căn hộ"

        services_str = ", ".join(services[:5]) + "..."  # Giới hạn để không vượt ký tự
        return (
            f"Dạ, tour {context['country']} {price_info['days']} ngày cho {price_info['pax']} người:\n"
            f"Giá ~{per_pax_usd} USD/người, tổng {total_usd} USD (chưa vé máy bay).\n"
            f"Đã gồm: {services_str}\n"
            f"Giá em báo chỉ là giá tham khảo do em chưa nắm chi tiết về chương trình của anh/chị.\n"
            f"Anh/chị cần lịch trình chi tiết từng ngày không ạ?"
        )

tour_processor = TourPriceProcessor()