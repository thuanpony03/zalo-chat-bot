import requests
import json

def send_zalo_message(access_token, user_id, message):
    api_url = "https://openapi.zalo.me/v3/oa/message/text"
    headers = {
        "access_token": access_token,
        "Content-Type": "application/json"
    }
    data = {
        "recipient": {
            "user_id": user_id
        },
        "message": {
            "text": message
        }
    }
    response = requests.post(api_url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message: {response.text}")

# Thay thế bằng thông tin của bạn
access_token = "9QMq5-PuzqWaehCPuttqIIQaintfPfS-U-dQOEbFpZGkwEH_x5VyJr_PsXtl1jO8TQFDLjC_-NDLjCCjvZ35326ErJYo4yahCBoFU8Cwasm5ueDWXJgwLoA-WGY_AemA9F-MGPbra4uchhHnf0sUMmYbj7B638rBTeVCHDyUtKzOjjvzrpBFS6E_y5tvFEHQMkBpUfHxp4yqp_fHy63yH6ow-ttW3-9XOQt3JVWPq798dyn0XpJnPHMxnsQ8OyTj9jtTNxr4qK0dyFTIWp7RLp-4z0c24C9N9hA1TOOCXIOsZuLmgYYfL2grZrtg6f9SVfA8PSquapjBleqGypQRC2YBYH3pCAmrPh2u5lyglZPPhxWfp1VW37IpyGVXE-y6HuUZETq6xpiShFytOZVsx7LcvsVpI0"
user_id = "3273615087242629962"
message = "Hello from Python!"

send_zalo_message(access_token, user_id, message)