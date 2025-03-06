# Service for weather_service
# Created: 2025-03-04 23:44:55
# Author: thuanpony03

import os
import aiohttp
import json
from dotenv import load_dotenv

load_dotenv()

class WeatherService:
    def __init__(self):
        self.api_key = os.environ.get('WEATHER_API_KEY')
        if not self.api_key:
            print("Warning: WEATHER_API_KEY is not set in environment variables")
            self.api_key = "default_key"  # Fallback để tránh lỗi
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        
    async def get_weather(self, location):
        """Lấy thông tin thời tiết cho một địa điểm"""
        try:
            params = {
                'q': location,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'vi'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        weather_data = await response.json()
                        return weather_data
                    else:
                        print(f"Error fetching weather: {await response.text()}")
                        return None
        except Exception as e:
            print(f"Error in get_weather: {e}")
            return None
            
    def format_weather_message(self, weather_data):
        """Định dạng thông tin thời tiết thành tin nhắn văn bản"""
        if not weather_data:
            return "Không thể lấy thông tin thời tiết. Vui lòng thử lại sau."
            
        try:
            location = weather_data["name"]
            country = weather_data["sys"]["country"]
            temp = weather_data["main"]["temp"]
            feels_like = weather_data["main"]["feels_like"]
            humidity = weather_data["main"]["humidity"]
            wind_speed = weather_data["wind"]["speed"]
            weather_desc = weather_data["weather"][0]["description"]
            
            message = f"🌤️ THỜI TIẾT TẠI {location.upper()}, {country}\n\n"
            message += f"🌡️ Nhiệt độ: {temp}°C\n"
            message += f"🤔 Cảm giác như: {feels_like}°C\n"
            message += f"💧 Độ ẩm: {humidity}%\n"
            message += f"💨 Tốc độ gió: {wind_speed} m/s\n"
            message += f"☁️ Thời tiết: {weather_desc}\n"
            
            return message
        except Exception as e:
            print(f"Error formatting weather message: {e}")
            return "Rất tiếc, không thể hiển thị thông tin thời tiết."

# Khởi tạo service
weather_service = WeatherService()

