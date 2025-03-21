from flask import Flask, request, jsonify
import os
import json
import hmac
import hashlib
from dotenv import load_dotenv
from services.zalo_api import ZaloAPI
from services.message_handler import message_handler
from datetime import datetime
import redis
from services.database import db
import asyncio
from asgiref.wsgi import WsgiToAsgi  # Thêm để chuyển WSGI sang ASGI

load_dotenv()

app = Flask(__name__)
zalo_api = ZaloAPI()

# Redis client to track processed messages
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=1, decode_responses=True)
    redis_client.ping()
    print("Redis connected successfully")
except redis.ConnectionError:
    print("Warning: Redis not available. Deduplication will be disabled.")
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
    profile = zalo_api.get_user_profile("3273615087242629962")
    return jsonify({"api_status": profile})

@app.route('/webhook', methods=['GET', 'POST'])
async def webhook():
    if request.method == 'GET':
        return "Webhook is active!"
    
    if request.method == 'POST':
        data = request.json
        print(f"Received webhook: {data}")
        
        event_name = data.get('event_name')
        event_id = None
        timestamp = int(data.get('timestamp', 0)) / 1000
        
        if event_name == 'user_send_text' and 'message' in data:
            event_id = f"text:{data['message'].get('msg_id')}"
        elif event_name == 'follow' and 'follower' in data:
            follower_id = data['follower'].get('id')
            event_id = f"follow:{follower_id}:{data.get('timestamp')}"
        elif event_name == 'user_click_button' and 'message' in data:
            button_id = data['message'].get('button_id', '') if data['message'].get('button_id') else ''
            event_id = f"button:{button_id}:{data.get('timestamp')}"
        elif event_name == 'user_send_image' and 'sender' in data:
            sender_id = data['sender'].get('id')
            event_id = f"image:{sender_id}:{data.get('timestamp')}"
        else:
            event_id = f"event:{event_name}:{data.get('timestamp')}"
        
        if event_id:
            if redis_client.exists(f"event:{event_id}"):
                print(f"Skipping duplicate event: {event_id}")
                return jsonify({"status": "duplicate_skipped"}), 200
            
            current_time = datetime.now().timestamp()
            if (current_time - timestamp) > 300:
                print(f"Skipping old event: {event_id}, age: {current_time - timestamp} seconds")
                return jsonify({"status": "old_event_skipped"}), 200
            
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
                    zalo_api.send_typing_indicator(user_id)
                    
                    message = data['message']
                    await message_handler.process_message(message, user_id)
                    
                    print("Message added to queue, waiting for processing")
                    return jsonify({"status": "message_queued"}), 200
                else:
                    print("No text field in message")
                    return jsonify({"error": "No text in message"}), 400
                    
            elif event_name == 'follow':
                user_id = data['follower']['id']
                welcome_messages = [
                    "👋 Xin chào! Cảm ơn bạn đã theo dõi Passport Lounge.",
                    "Tôi là trợ lý ảo của Passport Lounge, chuyên cung cấp:",
                    "🌏 Tour du lịch nước ngoài",
                    "🛂 Dịch vụ visa và hộ chiếu",
                    "✈️ Đặt vé máy bay",
                    "Tôi có thể giúp gì cho bạn hôm nay?"
                ]
                for msg in welcome_messages:
                    try:
                        result = zalo_api.send_text_message(user_id, msg)
                        if "error" in result:
                            print(f"Failed to send welcome message '{msg}': {result}")
                            continue
                        await asyncio.sleep(1)
                    except Exception as e:
                        print(f"Error sending welcome message '{msg}': {e}")
                        continue
                return jsonify({"status": "success"}), 200
                
            elif event_name == 'user_send_image':
                user_id = data['sender']['id']
                response = "Tôi đã nhận được hình ảnh của bạn. Tuy nhiên, tôi chỉ có thể xử lý tin nhắn văn bản. Vui lòng gửi yêu cầu bằng văn bản."
                try:
                    result = zalo_api.send_text_message(user_id, response)
                    if "error" in result:
                        return jsonify({"error": "Failed to send response", "details": result}), 500
                except Exception as e:
                    print(f"Error sending image response: {e}")
                return jsonify({"status": "success"}), 200
            
            return jsonify({"status": "unhandled_event"}), 200
            
        except Exception as e:
            print(f"Error processing webhook: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

# Giữ nguyên các route khác (/api/visa-products, /api/consultation-request)

# Chuyển Flask WSGI sang ASGI
asgi_app = WsgiToAsgi(app)

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(asgi_app, host='0.0.0.0', port=port)