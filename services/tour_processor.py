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
        """Phân tích hội thoại tour bằng AI với sự linh hoạt và chuyên nghiệp."""
        try:
            context_key = f"context:{user_id}"
            history_key = f"history:{user_id}"
            current_context = json.loads(redis_client.get(context_key) or '{}')
            history = json.loads(redis_client.get(history_key) or '[]')[-10:]

            # Định dạng lịch sử để AI dễ đọc
            history_formatted = ""
            for msg in history:
                if msg.startswith("User:"):
                    history_formatted += f"Khách: {msg[5:].strip()}\n"
                elif msg.startswith("Bot:"):
                    history_formatted += f"Bot: {msg[4:].strip()}\n"

            # Prompt AI cải tiến để tự nhiên và linh hoạt hơn
            prompt = (
                "Bạn là trợ lý AI chuyên nghiệp, thân thiện, tư vấn tour du lịch và visa bằng tiếng Việt.\n"
                "Hãy giao tiếp tự nhiên, thuyết phục như một nhân viên tư vấn thực thụ.\n\n"
                
                f"**Lịch sử hội thoại:**\n{history_formatted}\n\n"
                f"**Thông tin đã thu thập:**\n{json.dumps(current_context, ensure_ascii=False)}\n\n"
                f"**Tin nhắn hiện tại:**\n{user_query}\n\n"
                
                "**Nhiệm vụ của bạn:**\n"
                "1. Giữ và tích hợp thông tin đã biết (địa điểm, quốc gia, số người, số ngày).\n"
                "2. Hiểu ý định của khách qua ngữ cảnh, ví dụ:\n"
                "   - '1 tuần', '5 người', 'Nhật' -> tích hợp với thông tin trước đó.\n"
                "   - 'Có' hoặc 'muốn' sau câu hỏi về lịch trình -> khách đồng ý nhận chi tiết.\n"
                "   - Hỏi về dịch vụ không có trong gói (đảo, concert, yêu cầu đặc biệt) -> ghi nhận.\n"
                "3. Khi đủ thông tin (quốc gia/địa điểm, số ngày, số người) -> đề xuất báo giá.\n"
                "4. Nhận diện nhu cầu: tư vấn tour, visa, lịch trình chi tiết, hay yêu cầu đặc biệt.\n"
                "5. Nếu khách cần lịch trình chi tiết hoặc yêu cầu đặc biệt -> gợi ý để lại thông tin liên hệ.\n"
                "6. Trả lời tự nhiên, chuyên nghiệp, không lặp lại cứng nhắc.\n\n"
                
                "**Cần trả về JSON:**\n"
                "{\n"
                "  \"context\": {\n"
                "    \"locations\": [list các địa điểm],\n"
                "    \"country\": string,\n"
                "    \"days\": number,\n"
                "    \"pax\": number,\n"
                "    \"no_meal\": boolean,\n"
                "    \"upgrade_hotel\": boolean,\n"
                "    \"phone\": string,\n"
                "    \"reset\": boolean,\n"
                "    \"service_type\": string,\n"
                "    \"special_request\": string\n"
                "  },\n"
                "  \"intent\": {\n"
                "    \"request_price\": boolean,\n"
                "    \"consultation\": boolean,\n"
                "    \"confirmation\": boolean\n"
                "  },\n"
                "  \"ready_for_price\": boolean,\n"
                "  \"response\": string,\n"
                "  \"need_phone\": boolean\n"
                "}"
            )
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
            
            # Cập nhật context từ kết quả AI
            for key, value in result.get("context", {}).items():
                if value is not None:
                    current_context[key] = value

            # Lưu context và lịch sử vào Redis
            redis_client.set(context_key, json.dumps(current_context))
            history.append(f"User: {user_query}")
            redis_client.set(history_key, json.dumps(history[-10:]))

            return result

        except Exception as e:
            logger.error(f"Error in _analyze_conversation: {e}")
            return {
                "context": current_context,
                "intent": {"request_price": False, "consultation": True, "confirmation": False},
                "ready_for_price": False,
                "response": "Dạ, em chưa hiểu rõ lắm. Anh/chị có thể chia sẻ thêm thông tin để em hỗ trợ tốt hơn nhé!",
                "need_phone": False
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
        """Xử lý truy vấn của người dùng với sự chuyên nghiệp và linh hoạt."""
        try:
            analysis = await self._analyze_conversation(user_query, user_id)
            context = json.loads(redis_client.get(f"context:{user_id}") or '{}')
            
            # Cập nhật context từ analysis
            for key, value in analysis.get("context", {}).items():
                if value is not None:
                    context[key] = value
            redis_client.set(f"context:{user_id}", json.dumps(context))
            
            # Xử lý reset
            if context.get("reset"):
                new_context = {"country": None, "days": None, "pax": None, "no_meal": False, "phone": None, "reset": False, "special_request": None}
                redis_client.set(f"context:{user_id}", json.dumps(new_context))
                redis_client.delete(f"history:{user_id}")
                return ["Dạ, em đã reset thông tin. Anh/chị có thể bắt đầu lại nhé!"], new_context
            
            # Xử lý số điện thoại
            phone_pattern = r'(0[0-9]{9,10})|(\+84[0-9]{9,10})'
            phone_matches = re.findall(phone_pattern, user_query)
            if phone_matches:
                phone_number = phone_matches[0][0] or phone_matches[0][1]
                context["phone"] = phone_number
                self._save_customer_lead(user_id, context)
                response = f"Cảm ơn anh/chị đã để lại số {phone_number}. Nhân viên sẽ liên hệ ngay để hỗ trợ chi tiết ạ!"
                return self._split_message(response), context
            
            # Xử lý khi cần thông tin liên hệ (lịch trình chi tiết hoặc yêu cầu đặc biệt)
            if analysis.get("need_phone", False):
                response = analysis["response"] if "response" in analysis else (
                    "Dạ, để hỗ trợ chi tiết hơn, anh/chị vui lòng để lại tên và số điện thoại hoặc gọi hotline 1900 636563. "
                    "Nhân viên tư vấn sẽ liên hệ ngay để giải đáp và thiết kế tour theo nhu cầu của mình ạ!"
                )
                messages = self._split_message(response)
                redis_client.set(f"history:{user_id}", json.dumps(
                    json.loads(redis_client.get(f"history:{user_id}") or '[]')[-4:] + [f"Bot: {response}"]
                ))
                return messages, context
            
            # Tính giá khi đủ thông tin
            if analysis["ready_for_price"] and context.get("country") and context.get("pax") and context.get("days"):
                price_info = self._calculate_tour_price(
                    context["country"],
                    context["pax"],
                    context["days"],
                    context.get("no_meal", False)
                )
                response = self._build_price_response(price_info, context)
                messages = self._split_message(response)
                redis_client.set(f"history:{user_id}", json.dumps(
                    json.loads(redis_client.get(f"history:{user_id}") or '[]')[-4:] + [f"Bot: {response}"]
                ))
                return messages, context
            
            # Phản hồi mặc định từ AI
            response = analysis.get("response", "Dạ, em cần thêm thông tin về địa điểm, số người hoặc số ngày để tư vấn chính xác hơn. Anh/chị vui lòng chia sẻ thêm nhé!")
            messages = self._split_message(response)
            return messages, context

        except Exception as e:
            logger.error(f"Error in process_tour_query: {e}")
            return ["Dạ, hệ thống gặp chút trục trặc. Anh/chị vui lòng thử lại nhé!"], json.loads(redis_client.get(f"context:{user_id}") or '{}')

    def _calculate_tour_price(self, country, pax, days, no_meal):
        """Tính toán giá tour dựa trên giá cơ bản 1 người/ngày."""
        region = self._get_region_from_country(country)
        pricing = self.tour_pricing["pricing"].get(region, self.tour_pricing["pricing"]["asia_high"])
        
        tier = next((t for t in pricing if t["pax"][0] <= pax <= t["pax"][1]), pricing[-1])
        base_price_per_day = tier["base_price_short"]

        if days >= tier["long_days"]:
            discount = tier["long_price_discount_percentage"] / 100
            base_price_per_day *= (1 - discount)

        total_price_per_day_per_pax = base_price_per_day + (tier["no_meal_discount"] if no_meal else 0)
        total_price = total_price_per_day_per_pax * days * pax
        total_price_per_pax = total_price_per_day_per_pax * days

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
                "service_type": context.get("service_type", "tour"),
                "country_interest": context.get("country", ""),
                "description": f"{context.get('country', '')}, {context.get('days', 'chưa xác định')} ngày, {context.get('pax', 'chưa xác định')} người, yêu cầu đặc biệt: {context.get('special_request', 'không')}"
            }
            db.get_collection("leads").insert_one(lead_data)
            logger.info(f"Đã lưu lead: {context['phone']}")
        except Exception as e:
            logger.error(f"Error saving lead: {e}")

    def _build_price_response(self, price_info, context):
        """Tạo phản hồi giá tour chi tiết, thuyết phục và tự nhiên."""
        total_usd = round(price_info["total_price"])
        per_pax_usd = round(price_info["total_price_per_pax"])
        services = self.tour_pricing["default_services"].copy()
        if context.get("no_meal"):
            services[services.index("Ăn sáng tại khách sạn/căn hộ và 2 bữa chính")] = "Ăn sáng tại khách sạn/căn hộ"

        services_str = ", ".join(services[:5]) + "..."
        return (
            f"Dạ, với tour {context['country']} {price_info['days']} ngày cho {price_info['pax']} người, giá tham khảo khoảng {per_pax_usd} USD/người, tổng {total_usd} USD (chưa bao gồm vé máy bay).\n"
            f"Đã gồm: {services_str}\n"
            f"Đây là giá ước tính dựa trên thông tin anh/chị cung cấp. Nếu cần lịch trình chi tiết hoặc điều chỉnh theo nhu cầu riêng, anh/chị có muốn em hỗ trợ thêm không ạ?"
        )

tour_processor = TourPriceProcessor()