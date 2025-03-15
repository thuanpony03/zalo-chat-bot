# Main application entry point with Flask webhook
# Created: 2025-03-04 23:44:55
# Author: thuanpony03

from flask import Flask, request, jsonify
import os
import json
import hmac
import hashlib
from dotenv import load_dotenv
from services.zalo_api import ZaloAPI
from services.message_handler import message_handler
from datetime import datetime, timedelta
import redis
from services.database import db

load_dotenv()

app = Flask(__name__)
zalo_api = ZaloAPI()

# Redis client to track processed messages
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=1)
    # Kiểm tra kết nối
    redis_client.ping()
    print("Redis connected successfully")
except redis.ConnectionError:
    print("Warning: Redis not available. Deduplication will be disabled.")
    # Tạo một đối tượng giả lập redis để tránh lỗi
    class FakeRedis:
        def exists(self, key): return False
        def setex(self, key, time, value): pass
    redis_client = FakeRedis()

CACHE_EXPIRY = 300  # 5 minutes in seconds

@app.route('/')
def index():
    return "Thuận Pony Travel - Zalo Chatbot is running!"

@app.route('/api_test', methods=['GET'])
def api_test():
    """Endpoint test để kiểm tra kết nối với Zalo API"""
    profile = zalo_api.get_user_profile("3273615087242629962")  # Dùng user_id từ log
    return jsonify({"api_status": profile})

@app.route('/webhook', methods=['GET', 'POST'])
async def webhook():
    if request.method == 'GET':
        return "Webhook is active!"
    
    if request.method == 'POST':
        data = request.json
        print(f"Received webhook: {data}")
        
        # Create a unique event ID for deduplication based on event type
        event_name = data.get('event_name')
        event_id = None
        timestamp = int(data.get('timestamp', 0)) / 1000  # Convert to seconds
        
        # Generate unique event ID based on event type
        if event_name == 'user_send_text' and 'message' in data:
            # For text messages, use the msg_id
            event_id = f"text:{data['message'].get('msg_id')}"
        elif event_name == 'follow' and 'follower' in data:
            # For follow events, use follower ID + timestamp
            follower_id = data['follower'].get('id')
            event_id = f"follow:{follower_id}:{data.get('timestamp')}"
        elif event_name == 'user_click_button' and 'message' in data:
            # For button clicks, use button_id + timestamp
            button_id = data['message'].get('button_id', '')
            event_id = f"button:{button_id}:{data.get('timestamp')}"
        elif event_name == 'user_send_image' and 'sender' in data:
            # For images, use sender ID + timestamp
            sender_id = data['sender'].get('id')
            event_id = f"image:{sender_id}:{data.get('timestamp')}"
        else:
            # For other events, use event name + timestamp
            event_id = f"event:{event_name}:{data.get('timestamp')}"
        
        # Skip processing if we've seen this event before
        if event_id:
            # Check if we've seen this event before
            if redis_client.exists(f"event:{event_id}"):
                print(f"Skipping duplicate event: {event_id}")
                return jsonify({"status": "duplicate_skipped"}), 200
            
            # Check if the event is too old (more than 5 minutes)
            current_time = datetime.now().timestamp()
            if (current_time - timestamp) > 300:  # 300 seconds = 5 minutes
                print(f"Skipping old event: {event_id}, age: {current_time - timestamp} seconds")
                return jsonify({"status": "old_event_skipped"}), 200
            
            # Add to Redis with expiry
            redis_client.setex(f"event:{event_id}", CACHE_EXPIRY, str(current_time))
        
        mac = request.headers.get('X-ZaloOA-Signature')
        if mac and not zalo_api.verify_webhook(data, mac):
            return jsonify({"error": "Invalid signature"}), 401
        
        try:
            event_name = data.get('event_name')
            
            if event_name == 'user_send_text':
                user_id = data['sender']['id']
                print(f"Processing message from user_id: {user_id}")
                
                if 'text' in data.get('message', {}):

                    # Gửi typing indicator để tạo cảm giác chat thực tế
                    zalo_api.send_typing_indicator(user_id)
                    
                    message = data['message']['text']
                    response = await message_handler.process_message(user_id, message)
                    
                    print(f"Sending response: {response}")
                    result = zalo_api.send_text_message(user_id, response)
                    print(f"API response: {result}")
                    
                    if "error" in result:
                        return jsonify({"error": "Failed to send message", "details": result}), 500
                    return jsonify({"status": "success"}), 200
                else:
                    print("No text field in message")
                    return jsonify({"error": "No text in message"}), 400
                    
            elif event_name == 'user_click_button':
                user_id = data['sender']['id']
                button_id = data['message']['button_id']
                return jsonify({"status": "success"}), 200
                
            elif event_name == 'follow':
                user_id = data['follower']['id']
                welcome_message = (
                    "👋 Xin chào! Cảm ơn bạn đã theo dõi Passport Lounge.\n\n"
                    "Tôi là trợ lý ảo của Passport Lounge, chuyên cung cấp:\n"
                    "🌏 Tour du lịch nước ngoài\n"
                    "🛂 Dịch vụ visa và hộ chiếu\n"
                    "✈️ Đặt vé máy bay\n\n"
                    "Tôi có thể giúp gì cho bạn hôm nay?"
                )
                result = zalo_api.send_text_message(user_id, welcome_message)
                if "error" in result:
                    return jsonify({"error": "Failed to send welcome message", "details": result}), 500
                return jsonify({"status": "success"}), 200
                
            elif event_name == 'user_send_image':
                user_id = data['sender']['id']
                response = "Tôi đã nhận được hình ảnh của bạn. Tuy nhiên, tôi chỉ có thể xử lý tin nhắn văn bản. Vui lòng gửi yêu cầu bằng văn bản."
                result = zalo_api.send_text_message(user_id, response)
                if "error" in result:
                    return jsonify({"error": "Failed to send response", "details": result}), 500
                return jsonify({"status": "success"}), 200
            
            return jsonify({"status": "unhandled_event"}), 200
            
        except Exception as e:
            print(f"Error processing webhook: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

@app.route('/api/visa-products', methods=['GET'])
def get_visa_products():
    """API để lấy danh sách sản phẩm visa"""
    try:
        country = request.args.get('country', '')
        
        query = {}
        if country:
            query["country"] = {"$regex": country, "$options": "i"}
        
        products = list(db.get_collection("visas").find(
            query, 
            {
                "country": 1, 
                "visa_type": 1, 
                "price": 1, 
                "duration": 1, 
                "visa_method": 1,
                "product_id": 1,
                "product_url": 1
            }
        ))
        
        # Convert ObjectId to string
        for product in products:
            product["_id"] = str(product["_id"])
        
        return jsonify({"products": products}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Thêm route API để xử lý form đăng ký tư vấn
@app.route('/api/consultation-request', methods=['POST'])
def submit_consultation_request():
    """API nhận thông tin khách hàng đăng ký tư vấn"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Missing request data"}), 400
            
        required_fields = ['name', 'phone', 'destination']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Tạo dữ liệu yêu cầu tư vấn
        consultation_data = {
            "name": data['name'],
            "phone": data['phone'],
            "destination": data['destination'],
            "visa_type": data.get('visa_type', 'Du lịch'),
            "planned_date": data.get('planned_date', ''),
            "message": data.get('message', ''),
            "special_case": data.get('special_case', False),
            "source": "Zalo Bot",
            "status": "new",
            "created_at": datetime.now()
        }
        
        # Lưu vào DB
        db.consultation_requests.insert_one(consultation_data)
        
        # Thông báo cho admin qua email hoặc SMS (implement later)
        
        return jsonify({"success": True, "message": "Yêu cầu tư vấn đã được gửi thành công!"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)