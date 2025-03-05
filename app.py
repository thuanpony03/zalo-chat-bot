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

# Nạp biến môi trường
load_dotenv()

app = Flask(__name__)
zalo_api = ZaloAPI()

@app.route('/')
def index():
    return "Thuận Pony Travel - Zalo Chatbot is running!"

@app.route('/webhook', methods=['GET', 'POST'])
async def webhook():
    if request.method == 'GET':
        # Xử lý yêu cầu xác thực webhook từ Zalo
        return "Webhook is active!"
    
    if request.method == 'POST':
        # Nhận dữ liệu từ Zalo
        data = request.json
        
        # Xác thực webhook (nếu cần)
        mac = request.headers.get('X-ZaloOA-Signature')
        if mac and not zalo_api.verify_webhook(data, mac):
            return jsonify({"error": "Invalid signature"}), 401
        
        try:
            # Xử lý các sự kiện
            event_name = data.get('event_name')
            
            if event_name == 'user_send_text':
                # Người dùng gửi tin nhắn văn bản
                user_id = data['sender']['id']
                message = data['message']['text']
                
                # Xử lý tin nhắn
                response = await message_handler.process_message(user_id, message)
                
                # Gửi phản hồi
                zalo_api.send_text_message(user_id, response)
                
                return jsonify({"status": "success"}), 200
                
            elif event_name == 'user_click_button':
                # Người dùng nhấp vào nút
                user_id = data['sender']['id']
                button_id = data['message']['button_id']
                
                # Xử lý sự kiện click button
                # TODO: Thêm xử lý các button khác nhau
                
                return jsonify({"status": "success"}), 200
                
            elif event_name == 'user_follow':
                # Người dùng follow OA
                user_id = data['follower']['id']
                
                # Gửi tin nhắn chào mừng
                welcome_message = "👋 Xin chào! Cảm ơn bạn đã theo dõi Thuận Pony Travel.\n\n" + \
                                  "Tôi là trợ lý ảo của Thuận Pony Travel, chuyên cung cấp:\n" + \
                                  "🌏 Tour du lịch nước ngoài\n" + \
                                  "🛂 Dịch vụ visa và hộ chiếu\n" + \
                                  "✈️ Đặt vé máy bay\n\n" + \
                                  "Tôi có thể giúp gì cho bạn hôm nay?"
                
                zalo_api.send_text_message(user_id, welcome_message)
                
                return jsonify({"status": "success"}), 200
                
            elif event_name == 'user_send_image':
                # Người dùng gửi hình ảnh
                user_id = data['sender']['id']
                
                # Gửi phản hồi
                response = "Tôi đã nhận được hình ảnh của bạn. Tuy nhiên, tôi chỉ có thể xử lý tin nhắn văn bản. Vui lòng gửi yêu cầu bằng văn bản."
                zalo_api.send_text_message(user_id, response)
                
                return jsonify({"status": "success"}), 200
            
            return jsonify({"status": "unhandled_event"}), 200
            
        except Exception as e:
            print(f"Error processing webhook: {e}")
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)