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
        self.app_id = os.environ.get('ZALO_APP_ID')
        self.secret_key = os.environ.get('ZALO_APP_SECRET')
        # self.access_token = os.environ.get('ZALO_ACCESS_TOKEN')
        self.access_token = "6QuAGGQI4d8OgGrF0vSHSngl3Ki9Z7aKJFS5MJwJR6PPy6y41RK6Ea7A6M4vyLyYGxOa7LtoU4GYkcK2CCGFUosHTXjnz0aW29fsQtFbDZiZe2bUFVbW1dEd35KIdsGkSlupN0-VK68KsKOyHfmFMGNuSICMeIf3JE1H9m2EHcP9on0v2UjoN6IrR08VoYvGOfTFQnZE2rb1adOy6VLXSMBD93G4eZmEJEL4RmAh1mjanNbR5fazDblJ8bC3ZpzhGi1X6ms876KNttG3MP4YJZN9Jmbba21G2T1OB6kM9aSPzcm9ISqeMp2iJMP3mWiZ3fWM7Md2Q64kjIidG-bpQm6CELPok49lB84L86dUV6WvfXO8VE9YP1wLBIPLxLby7BzQ0WNVJKzrY00S3-03OrUzPp4KYGfiAWqk2WUD5d8"
        # Change API version from v3.0 to v3
        self.base_url = "https://openapi.zalo.me/v3.0"
        
        if not all([self.app_id, self.secret_key, self.access_token]):
            raise ValueError("Missing required environment variables (ZALO_APP_ID, ZALO_APP_SECRET, ZALO_ACCESS_TOKEN)")

    def verify_webhook(self, data, mac):
        """Xác thực webhook từ Zalo"""
        data_str = json.dumps(data, sort_keys=True)
        hmac_obj = hmac.new(self.secret_key.encode(), data_str.encode(), hashlib.sha256)
        calculated_mac = hmac_obj.hexdigest()
        return calculated_mac == mac

    def send_text_message(self, user_id, message):
        """Gửi tin nhắn văn bản đến người dùng (sử dụng Message API v3)"""
        # The correct endpoint according to documentation
        url = f"{self.base_url}/oa/message/cs"
        
        headers = {
            'access_token': self.access_token,
            'Content-Type': 'application/json'
        }
        
        data = {
            "recipient": {
                "user_id": user_id
            },
            "message": {
                "text": message
            }
        }
        
        try:
            print(f"Sending request to: {url}")
            print(f"With headers: {headers}")
            print(f"With data: {data}")
            
            # Send the API request
            response = requests.post(url, headers=headers, json=data)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {response.headers}")
            print(f"Response Text: {response.text}")
            
            # Parse response
            if response.text:
                try:
                    json_response = response.json()
                    
                    # Check for error in the Zalo API response
                    if json_response.get("error") == 0:
                        # Success case
                        return json_response
                    else:
                        # Error reported by Zalo
                        return {
                            "error": json_response.get("error"),
                            "message": json_response.get("message", "Unknown error")
                        }
                except json.JSONDecodeError:
                    return {"error": f"Invalid JSON response: {response.text}", "status_code": response.status_code}
            else:
                return {"error": "Empty response", "status_code": response.status_code}
        except Exception as e:
            print(f"Error sending message: {e}")
            return {"error": str(e)}
        
    def send_quick_replies(self, user_id, text, quick_replies):
        """Gửi tin nhắn kèm các lựa chọn nhanh"""
        # Update quick replies endpoint
        url = f"{self.base_url}/oa/message/interactive"
        headers = {
            'Content-Type': 'application/json',
            'access_token': self.access_token
        }
        
        if not isinstance(quick_replies, list) or not all(isinstance(qr, dict) for qr in quick_replies):
            return {"error": "Invalid quick_replies format"}
        
        data = {
            "recipient": {
                "user_id": user_id
            },
            "message": {
                "text": text,
                "quick_replies": quick_replies
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.text:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"error": f"Invalid JSON response: {response.text}"}
            return {"error": "Empty response"}
        except Exception as e:
            return {"error": str(e)}
        
    def send_list_template(self, user_id, elements):
        """Gửi danh sách tùy chọn dạng template"""
        url = f"{self.base_url}/oa/message/template"
        headers = {
            'Content-Type': 'application/json',
            'access_token': self.access_token
        }
        
        if not isinstance(elements, list) or not all(isinstance(el, dict) for el in elements):
            return {"error": "Invalid elements format"}
        
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
        
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.text:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"error": f"Invalid JSON response: {response.text}"}
            return {"error": "Empty response"}
        except Exception as e:
            return {"error": str(e)}

    def get_user_profile(self, user_id):
        """Lấy thông tin người dùng"""
        url = f"{self.base_url}/oa/getprofile"
        headers = {
            'access_token': self.access_token
        }
        params = {
            "user_id": user_id
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            print(f"Get Profile Status Code: {response.status_code}")
            print(f"Get Profile Response: {response.text}")
            if response.text:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"error": f"Invalid JSON response: {response.text}"}
            return {"error": "Empty response"}
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return {"error": str(e)}
    
    def check_token(self):
        """Kiểm tra trạng thái access token"""
        url = f"{self.base_url}/oa/getoa"
        headers = {
            'access_token': self.access_token
        }
        
        try:
            response = requests.get(url, headers=headers)
            return {
                "valid": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}



    # Thêm vào services/zalo_api.py class
    def send_typing_indicator(self, user_id):
        """Gửi typing indicator tới người dùng"""
        url = f"{self.base_url}/oa/conversation"
        headers = {
            'access_token': self.access_token,
            'Content-Type': 'application/json'
        }
        
        data = {
            "recipient": {
                "user_id": user_id
            },
            "sender_action": "typing"
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            return response.json() if response.status_code == 200 else {"error": response.status_code}
        except Exception as e:
            return {"error": str(e)}