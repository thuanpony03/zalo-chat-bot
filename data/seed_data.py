# Replace your MongoDB connection code
import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to local MongoDB instance
try:
    client = MongoClient('mongodb://localhost:27017/')
    # Create/use travel_chatbot database
    db = client.travel_chatbot
    
    # Clear existing data
    db.locations.drop()
    db.tours.drop()
    db.visas.drop()
    db.passports.drop()
    db.flights.drop()
    db.faqs.drop()
    db.users.drop()
    db.conversations.drop()
    db.bookings.drop()
    
    print("Connected to local MongoDB successfully!")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    exit(1)
    exit()

db = client.travel_chatbot

# Xoá dữ liệu visa cũ
db.visas.delete_many({})

# Tiếp tục với phần còn lại của code...

# Tiếp tục với phần tạo dữ liệu như trong code của bạn...
# (Giữ nguyên phần còn lại)
# Tạo dữ liệu địa điểm
print("Tạo dữ liệu địa điểm...")
locations = [
    {
        "_id": ObjectId(),
        "name": "Nhật Bản",
        "country": "Nhật Bản",
        "description": "Đất nước mặt trời mọc với sự kết hợp hài hòa giữa truyền thống và hiện đại.",
        "popular_cities": ["Tokyo", "Osaka", "Kyoto", "Hokkaido"],
        "currency": "Yên",
        "language": "Tiếng Nhật",
        "timezone": "GMT+9",
        "visa_required": True,
        "best_time_to_visit": "Tháng 3-5 (mùa hoa anh đào) hoặc tháng 9-11 (mùa thu lá đỏ)",
        "created_at": datetime.now()
    },
    {
        "_id": ObjectId(),
        "name": "Hàn Quốc",
        "country": "Hàn Quốc",
        "description": "Đất nước với nền văn hóa K-pop sôi động, ẩm thực phong phú và công nghệ tiên tiến.",
        "popular_cities": ["Seoul", "Busan", "Jeju", "Incheon"],
        "currency": "Won",
        "language": "Tiếng Hàn",
        "timezone": "GMT+9",
        "visa_required": True,
        "best_time_to_visit": "Tháng 4-6 hoặc tháng 9-11",
        "created_at": datetime.now()
    },
    {
        "_id": ObjectId(),
        "name": "Singapore",
        "country": "Singapore",
        "description": "Quốc đảo hiện đại với kiến trúc ấn tượng, ẩm thực đa dạng và mua sắm tuyệt vời.",
        "popular_cities": ["Singapore"],
        "currency": "Đô la Singapore",
        "language": "Tiếng Anh, Tiếng Hoa, Tiếng Mã Lai, Tiếng Tamil",
        "timezone": "GMT+8",
        "visa_required": True,
        "best_time_to_visit": "Quanh năm",
        "created_at": datetime.now()
    },
    {
        "_id": ObjectId(),
        "name": "Mỹ",
        "country": "Mỹ",
        "description": "Đất nước rộng lớn với vô số điểm tham quan từ thành phố sôi động đến thiên nhiên hùng vĩ.",
        "popular_cities": ["New York", "Los Angeles", "Las Vegas", "San Francisco"],
        "currency": "Đô la Mỹ",
        "language": "Tiếng Anh",
        "timezone": "GMT-5 đến GMT-10",
        "visa_required": True,
        "best_time_to_visit": "Tùy theo khu vực, phổ biến là mùa xuân và mùa thu",
        "created_at": datetime.now()
    },
    {
        "_id": ObjectId(),
        "name": "Pháp",
        "country": "Pháp",
        "description": "Đất nước lãng mạn với nghệ thuật, kiến trúc và ẩm thực nổi tiếng thế giới.",
        "popular_cities": ["Paris", "Nice", "Lyon", "Marseille"],
        "currency": "Euro",
        "language": "Tiếng Pháp",
        "timezone": "GMT+1",
        "visa_required": True,
        "best_time_to_visit": "Tháng 4-6 hoặc tháng 9-10",
        "created_at": datetime.now()
    }
]

location_ids = {}
for location in locations:
    location_id = location["_id"]
    location_ids[location["name"]] = location_id
    db.locations.insert_one(location)

# Tạo dữ liệu tour
print("Tạo dữ liệu tour...")
tours = [
    {
        "name": "Khám phá Nhật Bản 6 ngày 5 đêm",
        "description": "Hành trình trải nghiệm văn hóa và cảnh quan tuyệt đẹp của Nhật Bản với các điểm đến nổi tiếng như Tokyo, Kyoto và Osaka.",
        "destination": location_ids["Nhật Bản"],
        "duration": "6 ngày 5 đêm",
        "price": 25000000,  # VNĐ
        "inclusions": [
            "Vé máy bay khứ hồi",
            "Khách sạn 4 sao",
            "Bữa ăn theo chương trình",
            "Hướng dẫn viên tiếng Việt",
            "Xe đưa đón",
            "Vé tham quan"
        ],
        "exclusions": [
            "Chi phí cá nhân",
            "Tiền tip",
            "Bảo hiểm du lịch",
            "Visa"
        ],
        "departure_dates": [
            datetime.now() + timedelta(days=30),
            datetime.now() + timedelta(days=60),
            datetime.now() + timedelta(days=90)
        ],
        "min_people": 10,
        "images": [
            "https://example.com/japan1.jpg",
            "https://example.com/japan2.jpg"
        ],
        "created_at": datetime.now()
    },
    {
        "name": "Seoul - Nami - Everland 5 ngày 4 đêm",
        "description": "Khám phá thủ đô Seoul sôi động, đảo Nami lãng mạn và công viên giải trí Everland.",
        "destination": location_ids["Hàn Quốc"],
        "duration": "5 ngày 4 đêm",
        "price": 18500000,  # VNĐ
        "inclusions": [
            "Vé máy bay khứ hồi",
            "Khách sạn 4 sao",
            "Bữa ăn theo chương trình",
            "Hướng dẫn viên tiếng Việt",
            "Xe đưa đón",
            "Vé tham quan"
        ],
        "exclusions": [
            "Chi phí cá nhân",
            "Tiền tip",
            "Bảo hiểm du lịch",
            "Visa"
        ],
        "departure_dates": [
            datetime.now() + timedelta(days=15),
            datetime.now() + timedelta(days=45),
            datetime.now() + timedelta(days=75)
        ],
        "min_people": 10,
        "images": [
            "https://example.com/korea1.jpg",
            "https://example.com/korea2.jpg"
        ],
        "created_at": datetime.now()
    },
    {
        "name": "Singapore - Sentosa 4 ngày 3 đêm",
        "description": "Khám phá Singapore hiện đại với những điểm tham quan nổi tiếng: Marina Bay Sands, Gardens by the Bay và đảo Sentosa.",
        "destination": location_ids["Singapore"],
        "duration": "4 ngày 3 đêm",
        "price": 15000000,  # VNĐ
        "inclusions": [
            "Vé máy bay khứ hồi",
            "Khách sạn 4 sao",
            "Bữa ăn theo chương trình",
            "Hướng dẫn viên tiếng Việt",
            "Xe đưa đón",
            "Vé tham quan"
        ],
        "exclusions": [
            "Chi phí cá nhân",
            "Tiền tip",
            "Bảo hiểm du lịch"
        ],
        "departure_dates": [
            datetime.now() + timedelta(days=20),
            datetime.now() + timedelta(days=50),
            datetime.now() + timedelta(days=80)
        ],
        "min_people": 8,
        "images": [
            "https://example.com/singapore1.jpg",
            "https://example.com/singapore2.jpg"
        ],
        "created_at": datetime.now()
    },
    {
        "name": "Khám phá bờ Đông Hoa Kỳ 9 ngày 8 đêm",
        "description": "Hành trình đến các thành phố lớn bờ Đông Hoa Kỳ: New York, Washington D.C, Philadelphia và Boston.",
        "destination": location_ids["Mỹ"],
        "duration": "9 ngày 8 đêm",
        "price": 89000000,  # VNĐ
        "inclusions": [
            "Vé máy bay khứ hồi",
            "Khách sạn 4 sao",
            "Bữa ăn theo chương trình",
            "Hướng dẫn viên tiếng Việt",
            "Xe đưa đón",
            "Vé tham quan"
        ],
        "exclusions": [
            "Chi phí cá nhân",
            "Tiền tip",
            "Bảo hiểm du lịch",
            "Visa"
        ],
        "departure_dates": [
            datetime.now() + timedelta(days=45),
            datetime.now() + timedelta(days=90),
            datetime.now() + timedelta(days=135)
        ],
        "min_people": 10,
        "images": [
            "https://example.com/usa1.jpg",
            "https://example.com/usa2.jpg"
        ],
        "created_at": datetime.now()
    },
    {
        "name": "Paris - Monaco - Nice 7 ngày 6 đêm",
        "description": "Hành trình lãng mạn khám phá Paris hoa lệ, công quốc Monaco và thành phố biển Nice xinh đẹp.",
        "destination": location_ids["Pháp"],
        "duration": "7 ngày 6 đêm",
        "price": 65000000,  # VNĐ
        "inclusions": [
            "Vé máy bay khứ hồi",
            "Khách sạn 4 sao",
            "Bữa ăn theo chương trình",
            "Hướng dẫn viên tiếng Việt",
            "Xe đưa đón",
            "Vé tham quan"
        ],
        "exclusions": [
            "Chi phí cá nhân",
            "Tiền tip",
            "Bảo hiểm du lịch",
            "Visa"
        ],
        "departure_dates": [
            datetime.now() + timedelta(days=30),
            datetime.now() + timedelta(days=60),
            datetime.now() + timedelta(days=90)
        ],
        "min_people": 10,
        "images": [
            "https://example.com/france1.jpg",
            "https://example.com/france2.jpg"
        ],
        "created_at": datetime.now()
    }
]

for tour in tours:
    db.tours.insert_one(tour)

# Phần tạo dữ liệu visa với cấu trúc tối ưu


# Visa Trung Quốc
china_visa = {
    "_id": ObjectId(),
    "country": "Trung Quốc",
    "country_aliases": ["trung quoc", "trung quốc", "china", "tq", "trung"],
    "visa_type": "du lịch",
    "type_aliases": ["du lich", "du lịch", "tourist", "travel"],
    "price": 180,
    "duration": "90 ngày",
    "processing_time": "10-15 ngày làm việc",
    "success_rate": 98.6,
    "requirements": {
        "travel_docs": [
            "Hộ chiếu gốc còn hạn ít nhất 6 tháng",
            "Ảnh thẻ 4x6cm nền trắng chụp trong vòng 3 tháng",
            "Bản scan CCCD/CMND",
            "Đơn xin visa điền đầy đủ thông tin",
            "Giấy xác nhận thông tin cư trú – Mẫu CT07 hoặc Sổ hộ khẩu bản photo"
        ],
        "financial_docs": [
            "Sao kê tài khoản ngân hàng 3 tháng gần nhất",
            "Giấy tờ chứng minh công việc và thu nhập"
        ],
        "family_docs": [
            "Giấy đăng ký kết hôn (nếu đi cùng vợ/chồng)",
            "Giấy khai sinh (nếu đi cùng con)",
            "Giấy ủy quyền của cha mẹ (nếu trẻ em đi cùng 1 trong 2 người)"
        ]
    },
    "costs": {
        "options": [
            {"type": "Visa nhập cảnh 1 lần", "price": 180, "duration": "90 ngày"},
            {"type": "Visa nhập cảnh nhiều lần", "price": 300, "duration": "1 năm"}
        ],
        "includes": [
            "Phí lãnh sự quán",
            "Phí dịch vụ của Passport Lounge"
        ],
        "excludes": [
            "Phí bổ sung hồ sơ tài chính & thu nhập",
            "Phí xử lý nhanh"
        ]
    },
    "application_centers": [
        {
            "city": "Hồ Chí Minh",
            "address": "Phòng 1607-1609, tầng 16, Saigon Trade Center, 37 Tôn Đức Thắng, phường Bến Nghé, quận 1"
        },
        {
            "city": "Hà Nội",
            "address": "Tầng 7, tòa nhà Trường Thịnh, Tràng An Complex, số 1 Phùng Chí Kiên, phường Nghĩa Đô, quận Cầu Giấy"
        },
        {
            "city": "Đà Nẵng",
            "address": "Tầng 8, tòa nhà Indochina Riverside Towers, 74 Bạch Đằng, quận Hải Châu"
        }
    ],
    "benefits": [
        "Hỗ trợ hoàn thiện hồ sơ",
        "Không phí phát sinh",
        "Miễn phí nộp lại khi trượt",
        "Cam kết trước khi thực hiện"
    ],
    "process_steps": [
        {"name": "Đăng ký tư vấn", "description": "Trao đổi để thẩm định và đề xuất giải pháp tối ưu"},
        {"name": "Hoàn tất hồ sơ", "description": "1-2 ngày làm việc để hoàn chỉnh hồ sơ"},
        {"name": "Đặt lịch hẹn", "description": "Đặt lịch nộp hồ sơ tại trung tâm tiếp nhận"},
        {"name": "Nhận kết quả", "description": "Thông báo và gửi visa đến tận tay khách hàng"}
    ],
    "created_at": datetime.now(),
    "updated_at": datetime.now()
}

# Chèn dữ liệu vào database
# db.visas.insert_one(japan_visa)
db.visas.insert_one(china_visa)

print("Đã tạo dữ liệu visa Nhật Bản và Trung Quốc thành công!")

# Tạo dữ liệu hộ chiếu
print("Tạo dữ liệu hộ chiếu...")
passports = [
    {
        "service_type": "new",
        "requirements": [
            "Tờ khai đề nghị cấp hộ chiếu (mẫu X01)",
            "Chứng minh nhân dân/Căn cước công dân (bản gốc và bản sao)",
            "2 ảnh 4x6cm nền trắng",
            "Lệ phí"
        ],
        "processing_time": "7-10 ngày làm việc",
        "price": 700000,  # VNĐ (bao gồm phí dịch vụ)
        "validity": "10 năm",
        "notes": "Đối với hộ chiếu phổ thông. Cần có giấy tờ bổ sung nếu làm cho trẻ em dưới 14 tuổi.",
        "created_at": datetime.now()
    },
    {
        "service_type": "extend",
        "requirements": [
            "Tờ khai đề nghị gia hạn hộ chiếu",
            "Hộ chiếu gốc",
            "Chứng minh nhân dân/Căn cước công dân (bản gốc và bản sao)",
            "2 ảnh 4x6cm nền trắng",
            "Lệ phí"
        ],
        "processing_time": "7-10 ngày làm việc",
        "price": 600000,  # VNĐ (bao gồm phí dịch vụ)
        "validity": "Tùy theo từng trường hợp",
        "notes": "Hiện nay không còn dịch vụ gia hạn hộ chiếu, thay vào đó là làm hộ chiếu mới.",
        "created_at": datetime.now()
    },
    {
        "service_type": "replace",
        "requirements": [
            "Tờ khai đề nghị cấp lại hộ chiếu (mẫu X01)",
            "Chứng minh nhân dân/Căn cước công dân (bản gốc và bản sao)",
            "2 ảnh 4x6cm nền trắng",
            "Giấy báo mất (nếu bị mất)",
            "Hộ chiếu hư hỏng (nếu bị hỏng)",
            "Lệ phí"
        ],
        "processing_time": "7-10 ngày làm việc",
        "price": 800000,  # VNĐ (bao gồm phí dịch vụ)
        "validity": "10 năm",
        "notes": "Trường hợp mất hộ chiếu cần có giấy báo mất của cơ quan công an.",
        "created_at": datetime.now()
    }
]

for passport in passports:
    db.passports.insert_one(passport)

# Tạo dữ liệu FAQ
print("Tạo dữ liệu FAQ...")
faqs = [
    {
        "question": "Tôi cần chuẩn bị gì khi đi du lịch nước ngoài?",
        "answer": "Để chuẩn bị cho chuyến du lịch nước ngoài, bạn cần:\n1. Hộ chiếu còn hạn ít nhất 6 tháng\n2. Visa (nếu cần)\n3. Vé máy bay\n4. Xác nhận đặt phòng khách sạn\n5. Bảo hiểm du lịch\n6. Tiền mặt và thẻ thanh toán quốc tế\n7. Adapter sạc điện\n8. Bản sao giấy tờ quan trọng\n9. Thuốc cá nhân\n10. Quần áo phù hợp với thời tiết nơi đến",
        "created_at": datetime.now()
    },
    {
        "question": "Làm thế nào để đặt tour du lịch?",
        "answer": "Để đặt tour du lịch với Thuận Pony Travel, bạn có thể:\n1. Đặt trực tiếp qua chatbot này bằng cách nhập 'đặt tour'\n2. Liên hệ hotline: 1900xxxx\n3. Đến văn phòng công ty tại: 123 ABC, Quận X, TP.HCM\n4. Truy cập website: www.thuanponytravel.com\n\nSau khi đặt tour, nhân viên tư vấn sẽ liên hệ để xác nhận và hướng dẫn thanh toán trong vòng 24 giờ.",
        "created_at": datetime.now()
    },
    {
        "question": "Các hình thức thanh toán cho tour du lịch?",
        "answer": "Thuận Pony Travel chấp nhận các hình thức thanh toán sau:\n1. Tiền mặt tại văn phòng\n2. Chuyển khoản ngân hàng\n3. Thẻ tín dụng/ghi nợ\n4. Ví điện tử (Momo, ZaloPay, VNPay)\n\nKhi thanh toán, bạn cần đặt cọc 50% giá trị tour và thanh toán phần còn lại trước ngày khởi hành ít nhất 7 ngày.",
        "created_at": datetime.now()
    },
    {
        "question": "Chính sách hoàn hủy tour như thế nào?",
        "answer": "Chính sách hoàn/hủy tour của Thuận Pony Travel:\n- Hủy trước 30 ngày: hoàn 90% tổng giá trị\n- Hủy trước 15-29 ngày: hoàn 70% tổng giá trị\n- Hủy trước 7-14 ngày: hoàn 50% tổng giá trị\n- Hủy trước 1-6 ngày: hoàn 30% tổng giá trị\n- Ngày khởi hành: không hoàn tiền\n\nCác trường hợp bất khả kháng sẽ được xem xét riêng.",
        "created_at": datetime.now()
    },
    {
        "question": "Làm sao để xin visa Nhật Bản?",
        "answer": "Để xin visa Nhật Bản, bạn cần chuẩn bị những giấy tờ sau:\n1. Hộ chiếu còn hạn ít nhất 6 tháng\n2. Đơn xin visa (có chữ ký)\n3. 2 ảnh 4.5cm x 4.5cm nền trắng\n4. Lịch trình chuyến đi\n5. Vé máy bay khứ hồi (đặt trước)\n6. Xác nhận đặt phòng khách sạn\n7. Giấy xác nhận công việc\n8. Sao kê tài khoản ngân hàng 3 tháng gần nhất\n9. Bảo hiểm du lịch\n\nThuận Pony Travel có thể hỗ trợ bạn làm visa với chi phí 1,500,000 VNĐ, thời gian xử lý 5-7 ngày làm việc.",
        "created_at": datetime.now()
    },
    {
        "question": "Bảo hiểm du lịch quốc tế có những quyền lợi gì?",
        "answer": "Bảo hiểm du lịch quốc tế thường bao gồm những quyền lợi sau:\n1. Chi phí y tế và nằm viện (lên đến 1 tỷ VNĐ)\n2. Vận chuyển y tế khẩn cấp\n3. Hồi hương thi hài\n4. Trợ giúp pháp lý\n5. Mất hoặc hư hỏng hành lý\n6. Chuyến bay bị hoãn/hủy\n7. Mất giấy tờ du lịch\n8. Trách nhiệm cá nhân\n\nGiá thường từ 200,000-500,000 VNĐ cho 7-15 ngày tùy gói và quốc gia. Thuận Pony Travel có thể hỗ trợ bạn mua bảo hiểm du lịch phù hợp.",
        "created_at": datetime.now()
    },
    {
        "question": "Tôi có thể đổi ngoại tệ ở đâu?",
        "answer": "Bạn có thể đổi ngoại tệ tại:\n1. Ngân hàng (có tỷ giá tốt nhưng cần CMND/CCCD)\n2. Các điểm thu đổi ngoại tệ được cấp phép\n3. Sân bay (thuận tiện nhưng tỷ giá thường không tốt)\n\nChúng tôi khuyên bạn:\n- Đổi một phần tiền trước khi đi để chi tiêu ban đầu\n- Mang theo thẻ ATM/thẻ tín dụng quốc tế\n- Kiểm tra tỷ giá trước khi đổi\n- Giữ biên lai đổi tiền (một số quốc gia yêu cầu khi đổi ngược lại)",
        "created_at": datetime.now()
    },
    {
        "question": "Nên mang theo những vật dụng gì khi đi du lịch?",
        "answer": "Những vật dụng cần thiết khi đi du lịch nước ngoài:\n1. Giấy tờ: hộ chiếu, visa, bảo hiểm, vé máy bay, booking khách sạn\n2. Tiền và phương tiện thanh toán: tiền mặt, thẻ ATM/tín dụng quốc tế\n3. Thiết bị điện tử: điện thoại, sạc, pin dự phòng, adapter sạc\n4. Quần áo phù hợp với thời tiết và văn hóa nơi đến\n5. Thuốc cá nhân và y tế: thuốc thường dùng, băng cá nhân, thuốc chống say xe\n6. Vật dụng vệ sinh cá nhân\n7. Bản sao giấy tờ quan trọng (lưu riêng với bản gốc)\n8. Từ điển/ứng dụng dịch ngôn ngữ\n9. Bản đồ/ứng dụng bản đồ offline",
        "created_at": datetime.now()
    },
    {
        "question": "Làm thế nào để tránh bị jet lag?",
        "answer": "Để giảm thiểu tác động của jet lag khi đi du lịch qua nhiều múi giờ:\n1. Điều chỉnh đồng hồ sang múi giờ điểm đến ngay khi lên máy bay\n2. Cố gắng ngủ theo giờ của điểm đến\n3. Uống nhiều nước và tránh đồ uống có cồn và caffeine\n4. Ăn nhẹ và đúng bữa theo giờ điểm đến\n5. Tắm nắng buổi sáng tại nơi đến để cơ thể điều chỉnh nhịp sinh học\n6. Nếu đến vào buổi sáng, cố gắng thức đến tối\n7. Sử dụng mặt nạ ngủ và nút tai chống ồn khi cần ngủ\n8. Tập thể dục nhẹ sau khi đến nơi",
        "created_at": datetime.now()
    },
    {
        "question": "Làm hộ chiếu mới mất bao lâu?",
        "answer": "Thời gian làm hộ chiếu mới (passport) tại Việt Nam:\n- Thời gian xử lý thông thường: 7-10 ngày làm việc\n- Dịch vụ làm nhanh: 3-5 ngày làm việc (phụ phí)\n- Dịch vụ làm hỏa tốc: 1-2 ngày làm việc (phụ phí cao)\n\nThuận Pony Travel có thể hỗ trợ bạn làm hộ chiếu với chi phí từ 700,000 VNĐ, bao gồm phí dịch vụ và lệ phí hộ chiếu phổ thông.",
        "created_at": datetime.now()
    }
]

for faq in faqs:
    db.faqs.insert_one(faq)

print("Đã tạo dữ liệu mẫu thành công!")