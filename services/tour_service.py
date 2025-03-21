#!/usr/bin/env python3
"""
AI Processor for private tour pricing and consultation with optimized logic and persistent context.
"""
import asyncio
import json
import logging
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
        self.default_days = 5
        self.default_pax = 4

    def _load_tour_pricing_data(self):
        """Tải dữ liệu giá tour được cấu trúc với các khu vực và mức giá."""
        return {
            "asia_high": ["nhật bản|nhật|japan", "hàn quốc|hàn|korea"],
            "asia_low": ["thái lan|thailand|singapore|malaysia|indonesia|việt nam|philippines|campuchia|lào|myanmar"],
            "europe": ["châu âu|pháp|italy|đức|hà lan|spain|bồ đào nha|thụy sĩ|áo|paris|london|uk|england|scotland|ireland"],
            "oceania": ["úc|australia|new zealand|nz|oceania"],
            "america": ["mỹ|usa|hawaii|los angeles|new york|las vegas|san francisco|canada"],
            "pricing": {
                "asia_high": [
                    {"pax": (2, 3), "base_price": 420, "long_tour": {"days": 5, "discount": 0.05}, "no_meal": -40},
                    {"pax": (4, 6), "base_price": 380, "long_tour": {"days": 5, "discount": 0.05}, "no_meal": -40},
                    {"pax": (7, 10), "base_price": 330, "long_tour": {"days": 5, "discount": 0.04}, "no_meal": -40},
                    {"pax": (11, 16), "base_price": 290, "long_tour": {"days": 6, "discount": 0.03}, "no_meal": -40}
                ],
                "asia_low": [
                    {"pax": (2, 3), "base_price": 300, "long_tour": {"days": 5, "discount": 0.05}, "no_meal": -35},
                    {"pax": (4, 6), "base_price": 260, "long_tour": {"days": 5, "discount": 0.05}, "no_meal": -35},
                    {"pax": (7, 10), "base_price": 220, "long_tour": {"days": 5, "discount": 0.05}, "no_meal": -30},
                    {"pax": (11, 16), "base_price": 200, "long_tour": {"days": 6, "discount": 0.05}, "no_meal": -30}
                ],
                "europe": [
                    {"pax": (2, 3), "base_price": 450, "long_tour": {"days": 7, "discount": 0.04}, "no_meal": -60},
                    {"pax": (4, 6), "base_price": 430, "long_tour": {"days": 7, "discount": 0.04}, "no_meal": -60},
                    {"pax": (7, 10), "base_price": 400, "long_tour": {"days": 7, "discount": 0.04}, "no_meal": -55},
                    {"pax": (11, 16), "base_price": 380, "long_tour": {"days": 8, "discount": 0.03}, "no_meal": -55}
                ],
                "oceania": [
                    {"pax": (2, 3), "base_price": 450, "long_tour": {"days": 7, "discount": 0.04}, "no_meal": -60},
                    {"pax": (4, 6), "base_price": 430, "long_tour": {"days": 7, "discount": 0.04}, "no_meal": -60},
                    {"pax": (7, 10), "base_price": 400, "long_tour": {"days": 7, "discount": 0.04}, "no_meal": -55},
                    {"pax": (11, 16), "base_price": 380, "long_tour": {"days": 8, "discount": 0.03}, "no_meal": -55}
                ],
                "america": [
                    {"pax": (2, 3), "base_price": 480, "long_tour": {"days": 7, "discount": 0.04}, "no_meal": -80},
                    {"pax": (4, 6), "base_price": 460, "long_tour": {"days": 7, "discount": 0.04}, "no_meal": -80},
                    {"pax": (7, 10), "base_price": 420, "long_tour": {"days": 7, "discount": 0.04}, "no_meal": -70},
                    {"pax": (11, 16), "base_price": 380, "long_tour": {"days": 8, "discount": 0.03}, "no_meal": -60}
                ]
            },
            "default_services": ["xe riêng", "khách sạn 3-4*", "HDV", "ăn sáng + 2 bữa chính", "vé tham quan", "visa", "bảo hiểm", "eSIM"]
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
        """Phân tích hội thoại bằng AI với tối ưu hóa context."""
        try:
            context_key = f"context:{user_id}"
            history_key = f"history:{user_id}"
            current_context = json.loads(redis_client.get(context_key) or '{}')
            history = json.loads(redis_client.get(history_key) or '[]')[-5:]

            history_text = "\n".join(f"{'Khách' if h.startswith('User:') else 'Bot'}: {h[5:].strip() if h.startswith('User:') else h[4:].strip()}" for h in history)
            prompt = (
                f"Bạn là trợ lý AI phân tích hội thoại du lịch bằng tiếng Việt.\n\n"
                f"**Lịch sử hội thoại:**\n{history_text}\n\n"
                f"**Context hiện tại:**\n{json.dumps(current_context, ensure_ascii=False)}\n\n"
                f"**Tin nhắn mới:**\n{user_query}\n\n"
                "**Nhiệm vụ:**\n"
                "1. Tích hợp thông tin từ lịch sử và tin nhắn mới.\n"
                "2. Hiểu các câu ngắn như '5 người', '1 tuần', 'Nhật' dựa trên ngữ cảnh.\n"
                "3. Trả về JSON với context, intent, và response.\n\n"
                "**Kết quả mong muốn:**\n"
                "{{\n"
                "  \"context\": {{ \"country\": str, \"days\": int, \"pax\": int, \"no_meal\": bool, \"upgrade_hotel\": bool, \"phone\": str, \"reset\": bool }},\n"
                "  \"intent\": {{ \"request_price\": bool, \"consultation\": bool, \"confirmation\": bool }},\n"
                "  \"ready_for_price\": bool,\n"
                "  \"response\": str\n"
                "}}\n"
            )

            response = self.model.generate_content(prompt).text.strip()
            result = json.loads(response.replace("```json", "").replace("```", ""))

            new_context = result.get("context", {})
            for key, value in new_context.items():
                if value is not None or key not in current_context:
                    current_context[key] = value

            redis_client.set(context_key, json.dumps(current_context))
            history.append(f"User: {user_query}")
            redis_client.set(history_key, json.dumps(history[-5:]))

            return result

        except Exception as e:
            logger.error(f"Error in _analyze_conversation: {e}")
            return {
                "context": current_context,
                "intent": {"request_price": False, "consultation": True, "confirmation": False},
                "ready_for_price": False,
                "response": "Xin lỗi, hệ thống gặp lỗi. Anh/chị vui lòng thử lại nhé!"
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
        """Xử lý truy vấn của người dùng và trả về phản hồi cùng context mới."""
        try:
            analysis = await self._analyze_conversation(user_query, user_id)
            context = json.loads(redis_client.get(f"context:{user_id}") or '{}')
            
            for key, value in analysis.get("context", {}).items():
                if value is not None:
                    context[key] = value
                    
            redis_client.set(f"context:{user_id}", json.dumps(context))
            
            if context.get("reset"):
                redis_client.delete(f"context:{user_id}", f"history:{user_id}")
                response = "Đã reset trạng thái hội thoại. Bạn có thể bắt đầu lại với một câu hỏi mới."
                return [response], context
                
            if phone := context.get("phone"):
                self._save_customer_lead(user_id, context)
                response = f"Dạ, em đã ghi nhận SĐT {phone}. Nhân viên sẽ liên hệ anh/chị sớm ạ!"
                return [response], context
                
            if context.get("country") and context.get("pax"):
                price_info = self._calculate_tour_price(
                    context["country"],
                    context.get("pax", self.default_pax),
                    context.get("days", self.default_days),
                    context.get("no_meal", False),
                    context.get("upgrade_hotel", False)
                )
                response = self._build_price_response(price_info, context)
                messages = self._split_message(response)
                redis_client.set(f"history:{user_id}", json.dumps(
                    json.loads(redis_client.get(f"history:{user_id}") or '[]')[-4:] + [f"Bot: {response}"]
                ))
                return messages, context
                
            response = analysis.get("response", "Dạ, em chưa hiểu rõ yêu cầu. Anh/chị vui lòng cung cấp thêm thông tin về địa điểm, số người và số ngày đi nhé!")
            messages = self._split_message(response)
            redis_client.set(f"history:{user_id}", json.dumps(
                json.loads(redis_client.get(f"history:{user_id}") or '[]')[-4:] + [f"Bot: {response}"]
            ))
            return messages, context
            
        except Exception as e:
            logger.error(f"Error in process_tour_query: {e}")
            response = "Dạ, em bị lỗi chút xíu. Anh/chị hỏi lại nhé!"
            return [response], json.loads(redis_client.get(f"context:{user_id}") or '{}')

    def _calculate_tour_price(self, country, pax, days, no_meal, upgrade_hotel):
        """Tính toán giá tour dựa trên thông tin đầu vào với kiểm tra giá trị None."""
        pax = pax if pax is not None else self.default_pax
        days = days if days is not None else self.default_days
        
        region = self._get_region_from_country(country)
        pricing = self.tour_pricing["pricing"].get(region, self.tour_pricing["pricing"]["asia_high"])
        tier = next((t for t in pricing if t["pax"][0] <= pax <= t["pax"][1]), pricing[-1])
        base_price = tier["base_price"]

        if days >= tier["long_tour"]["days"]:
            base_price *= (1 - tier["long_tour"]["discount"])

        total_price_per_day = base_price + (tier["no_meal"] if no_meal else 0) + (40 if upgrade_hotel else 0)
        total_price = total_price_per_day * days
        total_price_per_pax = total_price / pax

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
                "description": f"{context.get('country', '')}, {context.get('days', self.default_days)} ngày, {context.get('pax', self.default_pax)} người"
            }
            db.get_collection("leads").insert_one(lead_data)
            logger.info(f"Đã lưu lead: {context['phone']}")
        except Exception as e:
            logger.error(f"Error saving lead: {e}")

    def _build_price_response(self, price_info, context):
        """Tạo phản hồi giá tour chi tiết."""
        total_usd = round(price_info["total_price"])
        per_pax_usd = round(price_info["total_price_per_pax"])
        services = self.tour_pricing["default_services"].copy()
        if context.get("no_meal"):
            services[services.index("ăn sáng + 2 bữa chính")] = "ăn sáng"
        if context.get("upgrade_hotel"):
            services[services.index("khách sạn 3-4*")] = "khách sạn 5*"

        return (
            f"Dạ, tour {context.get('country')} {price_info['days']} ngày cho {price_info['pax']} người:\n"
            f"Giá khoảng {per_pax_usd} USD/người, tổng {total_usd} USD (chưa gồm vé máy bay).\n"
            f"Đã bao gồm: {', '.join(services)}.\n"
            f"Anh/chị để lại SĐT để em tư vấn chi tiết nhé!"
        )


tour_processor = TourPriceProcessor()
