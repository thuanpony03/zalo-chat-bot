#!/usr/bin/env python3
"""
AI Processor for handling private tour pricing and consultation with enhanced flexibility.
"""
import google.generativeai as genai
import asyncio
import logging
import re
import json
import redis
from functools import lru_cache
from datetime import datetime

from config import Config

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Khởi tạo Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)

class TourPriceProcessor:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.tour_pricing = self._load_tour_pricing_data()
        self.conversation_context = {}
        self.weather_info = {
            "nhật bản": "Tháng 4 là mùa xuân, nhiệt độ 10-20°C, hoa anh đào nở rộ, rất đẹp để tham quan.",
            "hàn quốc": "Tháng 4 là mùa xuân, nhiệt độ 10-20°C, có hoa anh đào và nhiều lễ hội hoa.",
            "úc": "Tháng 4 là mùa thu, nhiệt độ 15-25°C, thời tiết dễ chịu, phù hợp để tham quan."
        }
        self.festival_info = {
            "nhật bản": "Tháng 4 có lễ hội hoa anh đào (Hanami) trên khắp Nhật Bản, rất đông vui.",
            "hàn quốc": "Tháng 4 có lễ hội hoa anh đào ở nhiều nơi, rất đáng tham gia.",
            "úc": "Tháng 4 có lễ hội ánh sáng Vivid Sydney (diễn ra vào cuối tháng), rất đáng trải nghiệm."
        }
        self.family_tips = "Nếu đi cùng gia đình, anh/chị nên mang theo quần áo ấm vì thời tiết có thể se lạnh, chuẩn bị giày thoải mái cho trẻ em, và chọn khách sạn có không gian rộng rãi."

    def _load_tour_pricing_data(self):
        return {
            "nhật bản|hàn quốc": [
                {"pax": (3, 4), "base_price_short": 400.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -40.00, "guide_fee": 150.00, "note": "Tài xế kiêm HDV"},
                {"pax": (5, 6), "base_price_short": 360.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -40.00, "guide_fee": 150.00, "note": "Tài xế + HDV"},
                {"pax": (7, 10), "base_price_short": 320.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -40.00, "guide_fee": 150.00, "note": "Tài xế + HDV"},
                {"pax": (11, 16), "base_price_short": 280.00, "long_price_discount_percentage": 3.0, "no_meal_discount": -40.00, "guide_fee": 150.00, "note": "Tài xế + HDV"}
            ],
            "đông nam á|ấn độ|sri lanka": [
                {"pax": (3, 4), "base_price_short": 300.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -35.00, "guide_fee": 100.00, "note": "Tài xế + HDV"},
                {"pax": (5, 6), "base_price_short": 260.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -35.00, "guide_fee": 110.00, "note": "Tài xế + HDV"},
                {"pax": (7, 10), "base_price_short": 220.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -30.00, "guide_fee": 120.00, "note": "Tài xế + HDV"},
                {"pax": (11, 16), "base_price_short": 200.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -30.00, "guide_fee": 140.00, "note": "Tài xế + HDV"}
            ],
            "tây âu|úc|new zealand": [
                {"pax": (3, 4), "base_price_short": 450.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -60.00, "guide_fee": 200.00, "note": "Tài xế kiêm HDV"},
                {"pax": (5, 6), "base_price_short": 430.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -60.00, "guide_fee": 200.00, "note": "TàiIt xế kiêm HDV"},
                {"pax": (7, 10), "base_price_short": 400.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -55.00, "guide_fee": 220.00, "note": "Tài xế + HDV"},
                {"pax": (11, 16), "base_price_short": 380.00, "long_price_discount_percentage": 3.0, "no_meal_discount": -55.00, "guide_fee": 240.00, "note": "Tài xế + HDV"}
            ],
            "đông âu|thổ nhĩ kỳ|ai cập": [
                {"pax": (3, 4), "base_price_short": 400.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -50.00, "guide_fee": 150.00, "note": "Tài xế + HDV"},
                {"pax": (5, 6), "base_price_short": 360.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -50.00, "guide_fee": 160.00, "note": "Tài xế + HDV"},
                {"pax": (7, 10), "base_price_short": 320.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -45.00, "guide_fee": 180.00, "note": "Tài xế + HDV"},
                {"pax": (11, 16), "base_price_short": 300.00, "long_price_discount_percentage": 3.0, "no_meal_discount": -45.00, "guide_fee": 200.00, "note": "Tài xế + HDV"}
            ],
            "uk|anh": [
                {"pax": (3, 4), "base_price_short": 500.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -80.00, "guide_fee": 300.00, "note": "Tài xế kiêm HDV"},
                {"pax": (5, 6), "base_price_short": 480.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -80.00, "guide_fee": 300.00, "note": "Tài xế kiêm HDV"},
                {"pax": (7, 10), "base_price_short": 440.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -70.00, "guide_fee": 320.00, "note": "Tài xế + HDV"},
                {"pax": (11, 16), "base_price_short": 400.00, "long_price_discount_percentage": 3.0, "no_meal_discount": -70.00, "guide_fee": 340.00, "note": "Tài xế + HDV"}
            ],
            "mỹ|canada": [
                {"pax": (3, 4), "base_price_short": 480.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -80.00, "guide_fee": 300.00, "note": "Tài xế kiêm HDV"},
                {"pax": (5, 6), "base_price_short": 460.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -80.00, "guide_fee": 300.00, "note": "Tài xế kiêm HDV"},
                {"pax": (7, 10), "base_price_short": 420.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -70.00, "guide_fee": 320.00, "note": "Tài xế + HDV"},
                {"pax": (11, 16), "base_price_short": 380.00, "long_price_discount_percentage": 3.0, "no_meal_discount": -60.00, "guide_fee": 340.00, "note": "Tài xế + HDV"}
            ],
            "trung đông|châu phi|mông cổ": [
                {"pax": (3, 4), "base_price_short": 440.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -50.00, "guide_fee": 200.00, "note": "Tài xế + HDV"},
                {"pax": (5, 6), "base_price_short": 400.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -50.00, "guide_fee": 200.00, "note": "Tài xế + HDV"},
                {"pax": (7, 10), "base_price_short": 340.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -45.00, "guide_fee": 220.00, "note": "Tài xế + HDV"},
                {"pax": (11, 16), "base_price_short": 320.00, "long_price_discount_percentage": 3.0, "no_meal_discount": -45.00, "guide_fee": 240.00, "note": "Tài xế + HDV"}
            ],
            "đài loan|hong kong|nga": [
                {"pax": (3, 4), "base_price_short": 350.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -40.00, "guide_fee": 150.00, "note": "Tài xế + HDV"},
                {"pax": (5, 6), "base_price_short": 330.00, "long_price_discount_percentage": 5.0, "no_meal_discount": -40.00, "guide_fee": 160.00, "note": "Tài xế + HDV"},
                {"pax": (7, 10), "base_price_short": 280.00, "long_price_discount_percentage": 4.0, "no_meal_discount": -35.00, "guide_fee": 180.00, "note": "Tài xế + HDV"},
                {"pax": (11, 16), "base_price_short": 260.00, "long_price_discount_percentage": 3.0, "no_meal_discount": -35.00, "guide_fee": 200.00, "note": "Tài xế + HDV"}
            ],
        }

    async def _detect_intent_with_ai(self, user_query, conversation_history):
        try:
            history_str = "\n".join(conversation_history) if conversation_history else "Không có lịch sử hội thoại."
            prompt = (
                "Bạn là trợ lý AI tư vấn tour du lịch. Dựa trên câu hỏi hiện tại và lịch sử hội thoại, phân tích ý định của khách hàng và trả về JSON:\n"
                "- no_meal: Khách muốn bỏ bữa ăn (true/false, chỉ true nếu có từ khóa như 'không ăn', 'bỏ phần ăn', 'tự túc ăn', 'bỏ ăn')\n"
                "- no_esim: Khách không muốn dùng eSIM (true/false)\n"
                "- upgrade_hotel: Khách muốn nâng cấp khách sạn (true/false)\n"
                "- guide_from_start: Khách muốn HDV từ điểm xuất phát (true/false)\n"
                "- reset: Khách muốn reset hội thoại (true/false)\n"
                "- request_price: Khách yêu cầu báo giá (true/false, chỉ true nếu có từ khóa như 'báo giá', 'giá bao nhiêu')\n"
                "- ask_guide: Khách hỏi về hướng dẫn viên riêng (true/false, chỉ true nếu hỏi về thuê HDV không đi kèm tour)\n"
                "- ask_weather: Khách hỏi về thời tiết (true/false)\n"
                "- ask_festival: Khách hỏi về lễ hội (true/false)\n"
                "- ask_visa: Khách hỏi về visa (true/false)\n"
                "- ask_family_tips: Khách hỏi về lưu ý khi đi với gia đình hoặc trẻ em (true/false, chỉ true nếu hỏi rõ ràng về lưu ý, không tự động true khi có từ 'gia đình')\n"
                "- is_consultation: Khách yêu cầu tư vấn tour (true/false, true nếu có từ khóa như 'tư vấn', 'tư vấn tour')\n"
                f"Lịch sử hội thoại:\n{history_str}\n\n"
                f"Câu hỏi hiện tại:\n{user_query}\n\n"
                "Trả về JSON như: {'no_meal': false, 'upgrade_hotel': false, 'ask_guide': false, 'is_consultation': false, ...}. Phân tích tự nhiên, chỉ thay đổi khi có yêu cầu rõ ràng."
            )
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            if response_text.startswith("```json") and response_text.endswith("```"):
                response_text = response_text[7:-3].strip()
            intent_data = json.loads(response_text)
            logger.info(f"AI intent detection result: {intent_data}")
            return intent_data
        except json.JSONDecodeError as e:
            logger.error(f"AI returned invalid JSON: {e}. Raw response: {response.text if 'response' in locals() else 'No response'}")
            query_lower = user_query.lower()
            return {
                "no_meal": "bỏ phần ăn" in query_lower or "không ăn" in query_lower or "tự túc ăn" in query_lower or "bỏ ăn" in query_lower,
                "no_esim": "không cần esim" in query_lower or "bỏ esim" in query_lower,
                "upgrade_hotel": "nâng cấp khách sạn" in query_lower,
                "guide_from_start": "hdv từ đầu" in query_lower,
                "reset": "reset" in query_lower,
                "request_price": "báo giá" in query_lower or "giá bao nhiêu" in query_lower,
                "ask_guide": "hdv" in query_lower and ("thuê" in query_lower or "riêng" in query_lower or "chỉ cần hdv" in query_lower),
                "ask_weather": "thời tiết" in query_lower or "nhiệt độ" in query_lower,
                "ask_festival": "lễ hội" in query_lower or "sự kiện" in query_lower,
                "ask_visa": "visa" in query_lower or "cần visa không" in query_lower,
                "ask_family_tips": "trẻ em" in query_lower or "gia đình" in query_lower and "lưu ý" in query_lower,
                "is_consultation": "tư vấn" in query_lower
            }
        except Exception as e:
            logger.error(f"AI intent detection failed: {e}")
            return {
                "no_meal": False, "no_esim": False, "upgrade_hotel": False, "guide_from_start": False,
                "reset": False, "request_price": False, "ask_guide": False, "ask_weather": False,
                "ask_festival": False, "ask_visa": False, "ask_family_tips": False, "is_consultation": False
            }

    async def _generate_recommendation(self, user_context, conversation_history):
        """Sử dụng AI để đưa ra gợi ý tự nhiên dựa trên ngữ cảnh."""
        try:
            history_str = "\n".join(conversation_history) if conversation_history else "Không có lịch sử hội thoại."
            country = user_context.get('country', 'không xác định')
            days = user_context.get('days', 0)
            pax = user_context.get('pax', 0)
            no_meal = user_context.get('no_meal', False)
            no_esim = user_context.get('no_esim', False)

            prompt = (
                "Bạn là trợ lý AI tư vấn tour du lịch. Dựa trên thông tin tour và lịch sử hội thoại, đưa ra một gợi ý tự nhiên để nâng cao trải nghiệm của khách. Gợi ý phải ngắn gọn, tự nhiên, và phù hợp với ngữ cảnh.\n"
                f"- Quốc gia: {country}\n"
                f"- Số ngày: {days}\n"
                f"- Số người: {pax}\n"
                f"- Bỏ bữa ăn: {no_meal}\n"
                f"- Bỏ eSIM: {no_esim}\n"
                f"Lịch sử hội thoại:\n{history_str}\n\n"
                "Ví dụ gợi ý:\n"
                "- Nếu đi đông người (4 người trở lên): 'Đi cùng gia đình đông người, anh/chị có thể cân nhắc nâng cấp lên khách sạn 4 sao để thoải mái hơn.'\n"
                "- Nếu đi dài ngày (8 ngày trở lên): 'Hành trình 9 ngày khá dài, anh/chị có thể cân nhắc thêm dịch vụ HDV riêng để chuyến đi thuận tiện hơn.'\n"
                "- Nếu bỏ bữa ăn: 'Vì anh/chị tự túc ăn, mình gợi ý nên thử các nhà hàng địa phương nổi tiếng tại điểm đến nhé!'\n"
                "Trả về gợi ý dưới dạng văn bản ngắn gọn, không cần định dạng đặc biệt."
            )
            response = self.model.generate_content(prompt)
            recommendation = response.text.strip()
            if recommendation:
                return f"💡 {recommendation}"
            return ""
        except Exception as e:
            logger.error(f"AI recommendation generation failed: {e}")
            return ""

    async def process_tour_query(self, user_query, user_context=None):
        try:
            user_context = user_context or {}
            user_id = user_context.get('user_id', 'unknown')
            if user_id not in self.conversation_context:
                self.conversation_context[user_id] = []

            self.conversation_context[user_id].append(f"User: {user_query}")
            self.conversation_context[user_id] = self.conversation_context[user_id][-10:]

            intent = await self._detect_intent_with_ai(user_query, self.conversation_context[user_id])

            # Cập nhật user_context
            new_country = self._extract_country_from_query(user_query)
            if new_country:
                user_context['country'] = new_country
            new_days = self._extract_days_from_query(user_query)
            if new_days:
                user_context['days'] = new_days
            new_pax = self._extract_pax_from_query(user_query)
            if new_pax:
                user_context['pax'] = new_pax

            user_context.update({
                'no_meal': intent.get('no_meal', user_context.get('no_meal', False)),
                'no_esim': intent.get('no_esim', user_context.get('no_esim', False)),
                'upgrade_hotel': intent.get('upgrade_hotel', user_context.get('upgrade_hotel', False)),
                'guide_from_start': intent.get('guide_from_start', user_context.get('guide_from_start', False)),
                'user_id': user_id
            })

            if intent.get('reset'):
                user_context.clear()
                self.conversation_context[user_id] = []
                return "Đã reset trạng thái hội thoại. Bạn có thể bắt đầu lại với một câu hỏi mới.", {}

            phone_number = self._extract_phone_number(user_query)
            if phone_number:
                user_context['customer_phone'] = phone_number
                return f"Cảm ơn anh/chị đã để lại số {phone_number}. Tư vấn viên sẽ liên hệ ngay để hỗ trợ chi tiết về tour và lịch trình ạ!", user_context

            # Ưu tiên trả lời các câu hỏi ngoài lề nếu có yêu cầu rõ ràng
            if intent.get('ask_weather') and user_context.get('country'):
                country_lower = user_context['country'].lower()
                weather = self.weather_info.get(country_lower, "Hiện tại mình chưa có thông tin thời tiết chi tiết, anh/chị có thể kiểm tra thêm trên các ứng dụng thời tiết nhé!")
                return f"Dạ, tại {user_context['country']} vào tháng sau: {weather} Anh/chị có cần thêm thông tin gì không ạ?", user_context

            if intent.get('ask_festival') and user_context.get('country'):
                country_lower = user_context['country'].lower()
                festival = self.festival_info.get(country_lower, "Hiện tại mình chưa có thông tin về lễ hội, anh/chị có thể hỏi thêm tư vấn viên qua 1900 636563 nhé!")
                return f"Dạ, tại {user_context['country']} vào tháng sau: {festival} Anh/chị có cần thêm thông tin gì không ạ?", user_context

            if intent.get('ask_visa') and user_context.get('country'):
                visa_info = "Công dân Việt Nam cần xin visa du lịch để nhập cảnh. Phí visa khoảng 3-4 triệu đồng/người, thời gian xét duyệt 5-7 ngày làm việc."
                return f"Dạ, đi {user_context['country']} thì {visa_info} Anh/chị có muốn mình hỗ trợ làm visa không ạ?", user_context

            if intent.get('ask_family_tips'):
                return f"Dạ, {self.family_tips} Anh/chị có cần thêm thông tin gì không ạ?", user_context

            if intent.get('ask_guide') and user_context.get('country') and user_context.get('days'):
                price_info = self._calculate_tour_price(user_context['country'], user_context.get('pax', 1), user_context['days'], no_meal=False, upgrade_hotel=False, guide_from_start=False)
                if price_info:
                    guide_cost = price_info['guide_fee_per_day'] * user_context['days']
                    return (
                        f"Dạ, chi phí thuê HDV riêng tại {user_context['country']} là {price_info['guide_fee_per_day']} USD/ngày, "
                        f"tổng {guide_cost} USD cho {user_context['days']} ngày (cho cả đoàn). "
                        "Anh/chị có muốn đặt dịch vụ này không ạ? Vui lòng để lại SĐT hoặc gọi 1900 636563 để tư vấn thêm!"
                    ), user_context

            # Báo giá ngay nếu có từ khóa "tư vấn" hoặc "báo giá" và đủ thông tin
            if (intent.get('is_consultation') or intent.get('request_price')) and user_context.get('country') and user_context.get('days') and user_context.get('pax'):
                price_info = self._calculate_tour_price(user_context['country'], user_context['pax'], user_context['days'], user_context['no_meal'], user_context['upgrade_hotel'], user_context['guide_from_start'])
                if price_info:
                    # Nếu là tin nhắn điều chỉnh (sau khi đã báo giá lần đầu)
                    if user_context.get('tour_state') == 'complete' and (intent.get('no_meal') or intent.get('no_esim') or intent.get('upgrade_hotel')):
                        response = (
                            f"Dạ, tour private {user_context['country']} {user_context['days']} ngày cho {user_context['pax']} người"
                        )
                        if user_context['no_meal']:
                            response += ", tự túc ăn"
                        response += (
                            f": giá khoảng {price_info['total_price_per_pax']} USD/khách, tổng {price_info['total_group_price']} USD (chưa gồm vé máy bay).\n"
                        )
                        if user_context['no_meal']:
                            meal_discount_total = abs(price_info['meal_discount'])
                            response += f"(Đã giảm {meal_discount_total} USD/khách do không gồm bữa ăn chính.)\n"
                        if user_context['no_esim']:
                            response += "(Đã bỏ eSIM theo yêu cầu của anh/chị.)\n"
                        if user_context['upgrade_hotel']:
                            response += "(Đã bao gồm nâng cấp khách sạn theo yêu cầu, nhân viên tư vấn sẽ xác nhận chi tiết chi phí.)\n"
                        response += "Anh/chị có muốn tư vấn viên liên hệ để hỗ trợ chi tiết hơn không ạ? Vui lòng để lại SĐT hoặc gọi 1900 636563!"
                        self.conversation_context[user_id].append(f"Bot: {response}")
                        return response, user_context

                    # Báo giá lần đầu
                    services = ["visa", "xe riêng", "khách sạn 3-4*", "HDV suốt tuyến"]
                    if not user_context['no_meal']:
                        services.append("ăn sáng + 2 bữa chính")
                    services.extend(["vé tham quan", "bảo hiểm 50.000USD"])
                    if not user_context['no_esim']:
                        services.append("eSIM 1GB/ngày")

                    response = (
                        f"Dạ, tour private {user_context['country']} {user_context['days']} ngày cho {user_context['pax']} người: "
                        f"giá khoảng {price_info['total_price_per_pax']} USD/khách, tổng {price_info['total_group_price']} USD (chưa gồm vé máy bay).\n"
                        f"Đã bao gồm: {', '.join(services)}.\n"
                        f"☀️ Thời tiết tháng sau tại {user_context['country']}: {self.weather_info.get(user_context['country'].lower(), 'thời tiết dễ chịu, phù hợp để tham quan')}.\n"
                    )

                    # Sử dụng AI để đưa ra gợi ý tự nhiên
                    recommendation = await self._generate_recommendation(user_context, self.conversation_context[user_id])
                    if recommendation:
                        response += f"{recommendation}\n"

                    if user_context['no_meal']:
                        meal_discount_total = abs(price_info['meal_discount'])
                        response += f"(Đã giảm {meal_discount_total} USD/khách do không gồm bữa ăn chính.)\n"

                    if user_context['upgrade_hotel']:
                        response += "(Đã bao gồm nâng cấp khách sạn theo yêu cầu, nhân viên tư vấn sẽ xác nhận chi tiết chi phí.)\n"

                    if user_context['no_esim']:
                        response += "(Đã bỏ eSIM theo yêu cầu của anh/chị.)\n"

                    response += "Anh/chị có muốn tư vấn viên liên hệ để hỗ trợ chi tiết hơn không ạ? Vui lòng để lại SĐT hoặc gọi 1900 636563!"
                    self.conversation_context[user_id].append(f"Bot: {response}")
                    user_context['tour_state'] = 'complete'
                    return response, user_context

            # Hỏi thêm thông tin nếu thiếu
            missing_info = []
            if not user_context.get('country'):
                missing_info.append("nước đến")
            if not user_context.get('days'):
                missing_info.append("số ngày")
            if not user_context.get('pax'):
                missing_info.append("số người")
            if missing_info:
                return f"Anh/chị vui lòng cho biết thêm {', '.join(missing_info)} để mình báo giá chính xác hơn ạ!", user_context

            return "Anh/chị cần thêm thông tin gì để mình hỗ trợ ạ?", user_context

        except Exception as e:
            logger.error(f"Tour query processing failed: {e}")
            return "Xin lỗi, mình không thể xử lý yêu cầu này. Bạn vui lòng thử lại sau nhé!", user_context

    def _calculate_tour_price(self, country, pax, days, no_meal=False, upgrade_hotel=False, guide_from_start=False):
        """Calculate tour price based on country, pax, days, and preferences (excluding airfare, in USD)."""
        country_lower = country.lower()
        for region, pricing in self.tour_pricing.items():
            if any(c in country_lower for c in region.split('|')):
                for tier in pricing:
                    min_pax, max_pax = tier['pax']
                    if min_pax <= pax <= max_pax:
                        base_price_short = tier['base_price_short']
                        discount_percentage = tier['long_price_discount_percentage']
                        base_price_long = base_price_short * (1 - discount_percentage / 100)

                        if "nhật bản" in region or "hàn quốc" in region:
                            base_price = base_price_short if days < 8 else base_price_long
                        else:
                            base_price = base_price_short if days < 10 else base_price_long

                        if no_meal:
                            base_price += tier['no_meal_discount']

                        total_base_cost = base_price * days
                        total_price_per_pax = total_base_cost
                        total_group_price = total_price_per_pax * pax

                        return {
                            "base_price": base_price,
                            "days": days,
                            "pax": pax,
                            "total_price_per_pax": total_price_per_pax,
                            "total_group_price": total_group_price,
                            "guide_fee_per_day": tier['guide_fee'],
                            "meal_discount": tier['no_meal_discount'] * days if no_meal else 0,
                            "note": tier['note']
                        }
        return None

    def _extract_country_from_query(self, query):
        query_lower = query.lower()
        country_keywords = {
            "nhật bản": ["nhật", "japan", "nhat ban", "nhat", "jp"],
            "hàn quốc": ["hàn", "korea", "han quoc", "han", "south korea", "hq"],
            "đông nam á": ["đông nam á", "southeast asia", "thái lan", "singapore", "malaysia", "indonesia", "philippines", "đna"],
            "ấn độ": ["ấn độ", "india", "an do"],
            "sri lanka": ["sri lanka", "srilanka"],
            "tây âu": ["tây âu", "western europe", "pháp", "đức", "italy", "tây ban nha", "bồ đào nha", "hà lan", "bỉ", "thụy sĩ"],
            "úc": ["úc", "australia", "au", "úc châu"],
            "new zealand": ["new zealand", "nz", "niu di lân"],
            "đông âu": ["đông âu", "eastern europe", "ba lan", "hungary", "czech", "slovakia", "romania", "bulgaria"],
            "thổ nhĩ kỳ": ["thổ nhĩ kỳ", "turkey", "tho nhi ky"],
            "ai cập": ["ai cập", "egypt", "ai cap"],
            "uk": ["uk", "anh", "england", "britain", "united kingdom"],
            "mỹ": ["mỹ", "usa", "united states", "america", "hoa kỳ"],
            "canada": ["canada", "ca", "can"],
            "trung đông": ["trung đông", "middle east", "dubai", "uae", "qatar", "saudi", "iran", "iraq"],
            "châu phi": ["châu phi", "africa", "nam phi", "kenya", "morocco", "tanzania"],
            "mông cổ": ["mông cổ", "mongolia", "mong co"],
            "đài loan": ["đài loan", "taiwan", "dai loan"],
            "hong kong": ["hong kong", "hồng kông", "hk"],
            "nga": ["nga", "russia", "nước nga"],
        }
        for country, keywords in country_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return country
        return None

    def _extract_pax_from_query(self, query):
        query_lower = query.lower()
        match = re.search(r'(\d+)\s*(người|khách|pax|person)', query_lower)
        return int(match.group(1)) if match else None

    def _extract_days_from_query(self, query):
        query_lower = query.lower()
        week_match = re.search(r'(\d+)\s*(tuần|week)', query_lower)
        if week_match:
            weeks = int(week_match.group(1))
            return weeks * 7
        day_match = re.search(r'(\d+)\s*(ngày|day)', query_lower)
        return int(day_match.group(1)) if day_match else None

    def _extract_phone_number(self, text):
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

@lru_cache(maxsize=1000)
def is_duplicate_msg(msg_id, text):
    key = f"msg:{msg_id}:{hash(text)}"
    if redis_client.get(key):
        return True
    redis_client.setex(key, 3600, "1")
    return False

tour_processor = TourPriceProcessor()