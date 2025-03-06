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
access_token = "y6570xGMz7dnPa0DiHFtUFDWG0cx28yQ-nT3C-qbg4783NLXzJYHHD8GN7Jo8OrWjLPjMOXNtKYJNHbkqN7rGkDlBp6hQCOXhKm1B-j8iZItEaCsj2Y9788lFXc3ED4DeHyDFQLWtnYuSmW3kbBO1wDYDXQhT8e4aGL2Biqse5tEFKSjtIsL0iiZM0cD88zvc2Lc0u0pi1-XJNumYMMSHy4HT6RaOu5nst11QF1-Wc70RdCRq6Uu2lLA1GtEM-W3tKeS6Sbgm2ELRH0eqs2b1ST7UZp3MP8hrsf72zvBi3ZcGcqnebAYCx11PKdpSA5lqcTEMjSOaJJHQr8mr6ld0E1w6YgWJgSyXb9pBg5osrcJR2jgYsZ0VAWR5tJgDyDWg00VS8u5p7UETtbRhqQoNEPvKrobUuKlSKQ5GxK9y7a"
user_id = "3273615087242629962"
message = "Hello from Python!"

send_zalo_message(access_token, user_id, message)