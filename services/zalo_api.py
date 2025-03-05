# Service for zalo_api
# Created: 2025-03-04 23:44:55
# Author: thuanpony03

import requests
import json
import hmac
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

class ZaloAPI:
    def __init__(self):
        self.app_id = os.getenv('ZALO_APP_ID')
        self.secret_key = os.getenv('ZALO_APP_SECRET')
        self.access_token = os.getenv('ZALO_ACCESS_TOKEN')
        self.base_url = 'https://openapi.zalo.me/v2.0/oa'

    def verify_webhook(self, data, mac):
        """Xác thực webhook từ Zalo"""
        data_str = json.dumps(data)
        hmac_obj = hmac.new(self.secret_key.encode(), data_str.encode(), hashlib.sha256)
        calculated_mac = hmac_obj.hexdigest()
        return calculated_mac == mac

    def send_text_message(self, user_id, text):
        """Gửi tin nhắn văn bản đến người dùng"""
        url = f"{self.base_url}/message"
        headers = {
            'Content-Type': 'application/json',
            'access_token': self.access_token
        }
        data = {
            "recipient": {
                "user_id": user_id
            },
            "message": {
                "text": text
            }
        }
        
        response = requests.post(url, headers=headers, json=data)
        return response.json()
        
    def send_quick_replies(self, user_id, text, quick_replies):
        """Gửi tin nhắn kèm các lựa chọn nhanh"""
        url = f"{self.base_url}/message"
        headers = {
            'Content-Type': 'application/json',
            'access_token': self.access_token
        }
        data = {
            "recipient": {
                "user_id": user_id
            },
            "message": {
                "text": text,
                "quick_replies": quick_replies
            }
        }
        
        response = requests.post(url, headers=headers, json=data)
        return response.json()
        
    def send_list_template(self, user_id, elements):
        """Gửi danh sách tùy chọn dạng template"""
        url = f"{self.base_url}/message"
        headers = {
            'Content-Type': 'application/json',
            'access_token': self.access_token
        }
        data = {
            "recipient": {
                "user_id": user_id
            },
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "list",
                        "elements": elements
                    }
                }
            }
        }
        
        response = requests.post(url, headers=headers, json=data)
        return response.json()

    def get_user_profile(self, user_id):
        """Lấy thông tin người dùng"""
        url = f"{self.base_url}/getprofile"
        params = {
            "user_id": user_id,
            "access_token": self.access_token
        }
        
        response = requests.get(url, params=params)
        return response.json()