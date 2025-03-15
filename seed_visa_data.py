from datetime import datetime
from bson import ObjectId
from services.database import db

# Xóa dữ liệu visa cũ
db.get_collection("visas").delete_many({})


#Visa Chau A

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
        "Giấy tờ chuyến đi": [
            "Hộ chiếu gốc còn hạn ít nhất 6 tháng",
            "Ảnh thẻ 4x6cm nền trắng chụp trong vòng 3 tháng",
            "Bản scan CCCD/CMND",
            "Đơn xin visa điền đầy đủ thông tin",
            "Giấy xác nhận thông tin cư trú – Mẫu CT07 hoặc Sổ hộ khẩu bản photo"
        ],
        "Giấy tờ tài chính": [
            "Sao kê tài khoản ngân hàng 3 tháng gần nhất",
            "Giấy tờ chứng minh công việc và thu nhập"
        ],
        "Giấy tờ gia đình": [
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
    "terms": [
        "Phí dịch vụ, phí visa và các phí liên quan sẽ thanh toán 100% ngay khi ký hợp đồng.",
        "Passport Lounge không chịu trách nhiệm về quyết định từ chối visa.",
        "Không hoàn phí khi hồ sơ đã được nộp lên Đại Sứ Quán/Lãnh Sự Quán."
    ],
    "payment_methods": [
        {"name": "Chuyển khoản ngân hàng", "details": "CTY TNHH DU LỊCH VINHAROUND - Số TK: 0171003469686 - Vietcombank TPHCM"},
        {"name": "Thẻ tín dụng", "details": "Hỗ trợ trả góp 0% lãi suất"},
        {"name": "Ví MoMo", "details": "093-334-4646"}
    ],
    "created_at": datetime.now(),
    "updated_at": datetime.now()
}

## Add this code after the china_visa definition and before the db.insert_one line

# Visa Ấn Độ
india_visa = {
    "_id": ObjectId(),
    "country": "Ấn Độ",
    "country_aliases": ["an do", "ấn độ", "india", "in độ", "ấn"],
    "visa_type": "du lịch",
    "type_aliases": ["du lich", "du lịch", "tourist", "travel"],
    "price": 50,
    "duration": "90 ngày",
    "processing_time": "3-5 ngày làm việc",
    "success_rate": 98.6,
    "requirements": {
        "Giấy tờ cần thiết": [
            "Hộ chiếu còn hạn ít nhất 6 tháng",
            "Căn cước công dân",
            "Hình thẻ 4x6 nền trắng",
            "Một số thông tin cá nhân trong quá trình nộp hồ sơ",
            "Tất cả hồ sơ là file mềm"
        ]
    },
    "costs": {
        "options": [
            {"type": "Visa nhập cảnh 2 lần", "price": 50, "duration": "90 ngày"},
            {"type": "Visa nhập cảnh nhiều lần", "price": 100, "duration": "1 năm"},
            {"type": "Visa nhập cảnh nhiều lần", "price": 200, "duration": "5 năm"}
        ],
        "includes": [
            "Phí thị thực Đại sứ quán",
            "Phí dịch vụ của Passport Lounge"
        ],
        "excludes": [
            "Dịch vụ bổ sung hồ sơ tài chính & thu nhập"
        ]
    },
    "visa_method": "Visa điện tử",
    "application_method": "Nộp trực tuyến",
    "process_steps": [
        {"name": "Đăng ký tư vấn", "description": "10 phút trao đổi thông tin"},
        {"name": "Xử lý & nộp hồ sơ", "description": "Passport Lounge xử lý & nộp hồ sơ (1 ngày)"},
        {"name": "Duyệt hồ sơ", "description": "Lãnh sự quán duyệt hồ sơ (2 ngày)"},
        {"name": "Nhận kết quả", "description": "Passport Lounge nhận và gửi kết quả cho khách"}
    ],
    "benefits": [
        "Hỗ trợ hoàn thiện hồ sơ",
        "Không phí phát sinh",
        "Miễn phí nộp lại khi trượt",
        "Cam kết trước khi thực hiện"
    ],
    "terms": [
        "Phí dịch vụ, phí visa và các phí liên quan sẽ thanh toán 100% ngay khi ký hợp đồng.",
        "Passport Lounge không chịu trách nhiệm về quyết định từ chối visa.",
        "Không hoàn phí khi hồ sơ đã được nộp lên Đại Sứ Quán/Lãnh Sự Quán."
    ],
    "payment_methods": [
        {"name": "Chuyển khoản ngân hàng", "details": "CTY TNHH DU LỊCH VINHAROUND - Số TK: 0171003469686 - Vietcombank TPHCM"},
        {"name": "Thẻ tín dụng", "details": "Hỗ trợ trả góp 0% lãi suất"},
        {"name": "Ví MoMo", "details": "093-334-4646"}
    ],
    "created_at": datetime.now(),
    "updated_at": datetime.now()
}

# Visa Đài Loan
taiwan_visa = {
    "_id": ObjectId(),
    "country": "Đài Loan",
    "country_aliases": ["dai loan", "đài loan", "taiwan", "đài", "dai"],
    "visa_type": "du lịch",
    "type_aliases": ["du lich", "du lịch", "tourist", "travel"],
    "price": 150,
    "duration": "90 ngày",
    "processing_time": "10-14 ngày làm việc",
    "success_rate": 98.6,
    "requirements": {
        "Hồ sơ nhân thân": [
            "Hộ chiếu + hộ chiếu cũ (nếu có)",
            "Ảnh mềm cỡ 3,5*4,5cm",
            "CT07",
            "Đăng ký kết hôn nếu đi cùng vợ/chồng",
            "Giấy khai sinh của con (nếu đi cùng con dưới 12 tuổi)"
        ],
        "Hồ sơ chứng minh tài sản": [
            "Sổ tiết kiệm tối thiểu 5.000 USD và Xác nhận số dư sổ tiết kiệm bản gốc",
            "Giấy tờ khác: sổ đỏ, đăng ký ô tô (nếu có)"
        ],
        "Hồ sơ công việc & thu nhập": [
            "Nhân viên: Giấy xác nhận công việc, Sao kê lương 6 tháng",
            "Chủ doanh nghiệp: Đăng ký kinh doanh, Biên nhận thuế 3 tháng"
        ]
    },
    "costs": {
        "options": [
            {"type": "Visa dán nhập cảnh 1 lần", "price": 150, "duration": "90 ngày"},
            {"type": "eVisa khi khách có visa Châu Âu, Mỹ, Canada", "price": 0, "duration": "90 ngày"}
        ],
        "includes": [
            "Phí thị thực",
            "Phí dịch vụ của Passport Lounge (chụp ảnh, dịch thuật, in ấn, nhận & giao kết quả)"
        ],
        "excludes": [
            "Dịch vụ bổ sung hồ sơ tài chính & thu nhập"
        ]
    },
    "visa_method": "Visa dán hộ chiếu",
    "application_method": "Nộp trực tiếp ĐSQ/LSQ",
    "application_centers": [
        {
            "city": "TP. Hồ Chí Minh",
            "address": "336 Nguyễn Tri Phương, Phường 4, Quận 10, TP. Hồ Chí Minh"
        }
    ],
    "process_steps": [
        {"name": "Đăng ký tư vấn", "description": "10 phút trao đổi thông tin"},
        {"name": "Xử lý hồ sơ & đặt lịch", "description": "Passport Lounge xử lý hồ sơ & đặt lịch hẹn (3 ngày)"},
        {"name": "Nộp hồ sơ", "description": "Quý khách nộp hồ sơ (1 ngày)"},
        {"name": "Duyệt hồ sơ", "description": "Lãnh sự quán duyệt hồ sơ (10 ngày)"},
        {"name": "Nhận kết quả", "description": "Passport Lounge nhận kết quả"}
    ],
    "benefits": [
        "Hỗ trợ hoàn thiện hồ sơ",
        "Không phí phát sinh",
        "Miễn phí nộp lại khi trượt",
        "Cam kết trước khi thực hiện"
    ],
    "terms": [
        "Phí dịch vụ, phí visa và các phí liên quan sẽ thanh toán 100% ngay khi ký hợp đồng.",
        "Passport Lounge không chịu trách nhiệm về quyết định từ chối visa.",
        "Không hoàn phí khi hồ sơ đã được nộp lên Đại Sứ Quán/Lãnh Sự Quán."
    ],
    "payment_methods": [
        {"name": "Chuyển khoản ngân hàng", "details": "CTY TNHH DU LỊCH VINHAROUND - Số TK: 0171003469686 - Vietcombank TPHCM"},
        {"name": "Thẻ tín dụng", "details": "Hỗ trợ trả góp 0% lãi suất"},
        {"name": "Ví MoMo", "details": "093-334-4646"}
    ],
    "created_at": datetime.now(),
    "updated_at": datetime.now()
}

# Visa Hàn Quốc
korea_visa = {
    "_id": ObjectId(),
    "country": "Hàn Quốc",
    "country_aliases": ["han quoc", "hàn quốc", "korea", "hàn", "han"],
    "visa_type": "du lịch",
    "type_aliases": ["du lich", "du lịch", "tourist", "travel"],
    "price": 150,
    "duration": "90 ngày",
    "processing_time": "14 ngày làm việc",
    "success_rate": 98.6,
    "requirements": {
        "Hồ sơ nhân thân": [
            "Hộ chiếu + hộ chiếu cũ (nếu có)",
            "Ảnh mềm cỡ 3,5*4,5cm",
            "CT07",
            "Đăng ký kết hôn nếu đi cùng vợ/chồng",
            "Giấy khai sinh của con (nếu đi cùng con dưới 12 tuổi)"
        ],
        "Hồ sơ chứng minh tài sản": [
            "Sổ tiết kiệm tối thiểu 5.000 USD và Xác nhận số dư sổ tiết kiệm bản gốc",
            "Giấy tờ khác: sổ đỏ, đăng ký ô tô (nếu có)"
        ],
        "Hồ sơ công việc & thu nhập": [
            "Nhân viên: Giấy xác nhận công việc, Sao kê lương 6 tháng",
            "Chủ doanh nghiệp: Đăng ký kinh doanh, Biên nhận thuế 3 tháng"
        ]
    },
    "costs": {
        "options": [
            {"type": "Visa nhập cảnh 1 lần", "price": 150, "duration": "90 ngày"},
            {"type": "Visa nhập cảnh nhiều lần", "price": 300, "duration": "5 năm"},
            {"type": "Visa nhập cảnh 1 lần xin khẩn 7 ngày", "price": 250, "duration": "90 ngày"}
        ],
        "includes": [
            "Phí lãnh sự quán Hàn Quốc",
            "Phí dịch vụ của Passport Lounge (chụp ảnh, dịch thuật, in ấn, nhận & giao kết quả)"
        ],
        "excludes": [
            "Dịch vụ bổ sung hồ sơ tài chính & thu nhập"
        ]
    },
    "visa_method": "Visa điện tử",
    "application_method": "Nộp trực tiếp ĐSQ/LSQ",
    "process_steps": [
        {"name": "Đăng ký tư vấn", "description": "10 phút trao đổi thông tin"},
        {"name": "Xử lý & nộp hồ sơ", "description": "Passport Lounge xử lý & nộp hồ sơ (1-3 ngày)"},
        {"name": "Duyệt hồ sơ", "description": "Lãnh sự quán duyệt hồ sơ (14 ngày)"},
        {"name": "Nhận kết quả", "description": "Passport Lounge nhận kết quả"}
    ],
    "benefits": [
        "Hỗ trợ hoàn thiện hồ sơ",
        "Không phí phát sinh",
        "Miễn phí nộp lại khi trượt",
        "Cam kết trước khi thực hiện"
    ],
    "terms": [
        "Phí dịch vụ, phí visa và các phí liên quan sẽ thanh toán 100% ngay khi ký hợp đồng.",
        "Passport Lounge không chịu trách nhiệm về quyết định từ chối visa.",
        "Không hoàn phí khi hồ sơ đã được nộp lên Đại Sứ Quán/Lãnh Sự Quán."
    ],
    "payment_methods": [
        {"name": "Chuyển khoản ngân hàng", "details": "CTY TNHH DU LỊCH VINHAROUND - Số TK: 0171003469686 - Vietcombank TPHCM"},
        {"name": "Thẻ tín dụng", "details": "Hỗ trợ trả góp 0% lãi suất"},
        {"name": "Ví MoMo", "details": "093-334-4646"}
    ],
    "created_at": datetime.now(),
    "updated_at": datetime.now()
}

# Visa Hongkong
hongkong_visa = {
    "_id": ObjectId(),
    "country": "Hongkong",
    "country_aliases": ["hong kong", "hồng kông", "hk", "hong", "hồng"],
    "visa_type": "du lịch",
    "type_aliases": ["du lich", "du lịch", "tourist", "travel"],
    "price": 125,
    "duration": "90 ngày",
    "processing_time": "14-30 ngày làm việc",
    "success_rate": 98.6,
    "requirements": {
        "Hồ sơ cá nhân": [
            "Hộ chiếu gốc còn giá trị sử dụng ít nhất 6 tháng",
            "Hộ chiếu cũ (nếu có)",
            "Giấy khai sinh",
            "Căn cước công dân",
            "Giấy đăng ký kết hôn (nếu đã kết hôn)"
        ],
        "Hồ sơ chứng minh công việc": [
            "Nhân viên: Đơn xin nghỉ phép, Hợp đồng lao động, Bảng lương 3 tháng",
            "Chủ doanh nghiệp: Đăng ký kinh doanh, Biên lai thuế 3 tháng"
        ],
        "Hồ sơ chứng minh tài chính": [
            "Sổ đỏ, Giấy tờ mua bán nhà đất",
            "Xác nhận số dư tài khoản",
            "Giấy tờ sở hữu nhà đất, xe hơi, cổ phiếu"
        ],
        "Giấy tờ chuyến đi": [
            "Giấy xác nhận vé máy bay khứ hồi",
            "Giấy xác nhận đăng ký khách sạn",
            "Lịch trình du lịch",
            "Bảo hiểm chuyến đi"
        ]
    },
    "costs": {
        "options": [
            {"type": "Visa nhập cảnh 1 lần/2 lần/3 lần", "price": 125, "duration": "90 ngày"},
            {"type": "Visa nhập cảnh nhiều lần", "price": 220, "duration": "1-3 năm"}
        ],
        "includes": [
            "Phí visa của Sở Di Trú Hongkong",
            "Phí dịch vụ của Passport Lounge (chụp ảnh, dịch thuật, in ấn, nhận & giao kết quả)"
        ],
        "excludes": [
            "Dịch vụ bổ sung hồ sơ tài chính & thu nhập"
        ]
    },
    "visa_method": "Visa điện tử",
    "application_method": "Nộp trực tuyến",
    "process_steps": [
        {"name": "Đăng ký tư vấn", "description": "10 phút trao đổi thông tin"},
        {"name": "Xử lý & nộp hồ sơ", "description": "Passport Lounge xử lý & nộp hồ sơ (1-2 ngày)"},
        {"name": "Duyệt hồ sơ", "description": "Sở di trú Hongkong duyệt hồ sơ (14-30 ngày)"},
        {"name": "Nhận kết quả", "description": "Passport Lounge nhận kết quả"}
    ],
    "benefits": [
        "Hỗ trợ hoàn thiện hồ sơ",
        "Không phí phát sinh",
        "Miễn phí nộp lại khi trượt",
        "Cam kết trước khi thực hiện"
    ],
    "terms": [
        "Phí dịch vụ, phí visa và các phí liên quan sẽ thanh toán 100% ngay khi ký hợp đồng.",
        "Passport Lounge không chịu trách nhiệm về quyết định từ chối visa.",
        "Không hoàn phí khi hồ sơ đã được nộp lên Đại Sứ Quán/Lãnh Sự Quán."
    ],
    "payment_methods": [
        {"name": "Chuyển khoản ngân hàng", "details": "CTY TNHH DU LỊCH VINHAROUND - Số TK: 0171003469686 - Vietcombank TPHCM"},
        {"name": "Thẻ tín dụng", "details": "Hỗ trợ trả góp 0% lãi suất"},
        {"name": "Ví MoMo", "details": "093-334-4646"}
    ],
    "created_at": datetime.now(),
    "updated_at": datetime.now()
}

# Visa Nga
russia_visa = {
    "_id": ObjectId(),
    "country": "Nga",
    "country_aliases": ["nga", "russia", "liên bang nga", "lien bang nga", "russian"],
    "visa_type": "du lịch",
    "type_aliases": ["du lich", "du lịch", "tourist", "travel"],
    "price": 90,
    "duration": "60 ngày",
    "processing_time": "7 ngày làm việc",
    "success_rate": 98.6,
    "requirements": {
        "Hồ sơ nhân thân": [
            "Hộ chiếu + hộ chiếu cũ (nếu có)",
            "Ảnh mềm cỡ 3,5*4,5cm",
            "Scan bảo hiểm du lịch",
            "Scan booking khách sạn"
        ]
    },
    "costs": {
        "options": [
            {"type": "eVisa nhập cảnh 1 lần", "price": 90, "duration": "60 ngày"}
        ],
        "includes": [
            "Phí thị thực Đại sứ quán",
            "Phí dịch vụ của Passport Lounge"
        ],
        "excludes": [
            "Dịch vụ bổ sung hồ sơ tài chính & thu nhập"
        ]
    },
    "visa_method": "Visa điện tử",
    "application_method": "Nộp trực tuyến",
    "process_steps": [
        {"name": "Đăng ký tư vấn", "description": "10 phút trao đổi thông tin"},
        {"name": "Xử lý & nộp hồ sơ", "description": "Passport Lounge xử lý hồ sơ & nộp hồ sơ (3 ngày)"},
        {"name": "Duyệt hồ sơ", "description": "Lãnh sự quán duyệt hồ sơ (7 ngày)"},
        {"name": "Nhận kết quả", "description": "Passport Lounge nhận kết quả"}
    ],
    "benefits": [
        "Hỗ trợ hoàn thiện hồ sơ",
        "Không phí phát sinh",
        "Miễn phí nộp lại khi trượt",
        "Cam kết trước khi thực hiện"
    ],
    "terms": [
        "Phí dịch vụ, phí visa và các phí liên quan sẽ thanh toán 100% ngay khi ký hợp đồng.",
        "Passport Lounge không chịu trách nhiệm về quyết định từ chối visa.",
        "Không hoàn phí khi hồ sơ đã được nộp lên Đại Sứ Quán/Lãnh Sự Quán."
    ],
    "payment_methods": [
        {"name": "Chuyển khoản ngân hàng", "details": "CTY TNHH DU LỊCH VINHAROUND - Số TK: 0171003469686 - Vietcombank TPHCM"},
        {"name": "Thẻ tín dụng", "details": "Hỗ trợ trả góp 0% lãi suất"},
        {"name": "Ví MoMo", "details": "093-334-4646"}
    ],
    "created_at": datetime.now(),
    "updated_at": datetime.now()
}



#Visa Nhật Bản
japan_visa = {
    "_id": ObjectId(),
    "country": "Nhật Bản",
    "country_aliases": ["nhat ban", "nhật bản", "japan", "nhật", "jp"],
    "visa_type": "du lịch",
    "type_aliases": ["du lich", "du lịch", "tourist", "travel"],
    "price": 120,
    "duration": "90 ngày",
    "processing_time": "10 ngày làm việc",
    "success_rate": 98.6,
    "requirements": {
        "Giấy tờ nhân thân": [
            "Hộ chiếu gốc còn hạn ít nhất 6 tháng + Hộ chiếu cũ (nếu có)",
            "Giấy đăng ký kết hôn (nếu đi cùng vợ/chồng)",
            "Giấy khai sinh của con (nếu đi cùng con dưới 14 tuổi)"
        ],
        "Giấy tờ tài chính": [
            "Sổ tiết kiệm tối thiểu 5.000 USD hoặc Xác nhận số dư sổ tiết kiệm 120 triệu VND",
            "Giấy tờ khác: Sổ đỏ, đăng ký ô tô (nếu có)"
        ],
        "Giấy tờ công việc & thu nhập": [
            "Nếu là nhân viên: Giấy xác nhận công việc, Sao kê tài khoản trả lương 6 tháng gần nhất, Hợp đồng lao động & Xác nhận nghỉ phép, VssID thể hiện quá trình đóng BHXH",
            "Nếu là chủ doanh nghiệp: Đăng ký kinh doanh, Biên nhận nộp thuế 3 tháng gần nhất"
        ]
    },
    "costs": {
        "options": [
            {"type": "Visa nhập cảnh 1 lần", "price": 120, "duration": "90 ngày"},
            {"type": "Visa nhập cảnh nhiều lần", "price": 180, "duration": "1-5 năm"},
            {"type": "Visa quá cảnh 1 hoặc 2 lần", "price": 100, "duration": "90 ngày"}
        ],
        "includes": [
            "Phí lãnh sự quán Nhật Bản",
            "Phí dịch vụ của Passport Lounge (chụp ảnh, dịch thuật, in ấn, nhận & giao kết quả)"
        ],
        "excludes": [
            "Dịch vụ bổ sung hồ sơ tài chính & thu nhập"
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
    "terms": [
        "Phí dịch vụ, phí visa và các phí liên quan sẽ thanh toán 100% ngay khi ký hợp đồng.",
        "Passport Lounge không chịu trách nhiệm về quyết định từ chối visa.",
        "Không hoàn phí khi hồ sơ đã được nộp lên Đại Sứ Quán/Lãnh Sự Quán."
    ],
    "payment_methods": [
        {"name": "Chuyển khoản ngân hàng", "details": "CTY TNHH DU LỊCH VINHAROUND - Số TK: 0171003469686 - Vietcombank TPHCM"},
        {"name": "Thẻ tín dụng", "details": "Hỗ trợ trả góp 0% lãi suất"},
        {"name": "Ví MoMo", "details": "093-334-4646"}
    ],
    "created_at": datetime.now(),
    "updated_at": datetime.now()
}


#Visa Macau
macau_visa = {
    "_id": ObjectId(),
    "country": "Macau",
    "country_aliases": ["macau", "mặc dù", "ma cao", "macao"],
    "visa_type": "du lịch",
    "type_aliases": ["du lich", "du lịch", "tourist", "travel"],
    "price": 300,
    "duration": "90 ngày",
    "processing_time": "14 ngày làm việc",
    "success_rate": 98.6,
    "requirements": {
        "Giấy tờ nhân thân": [
            "Hộ chiếu gốc còn hạn ít nhất 6 tháng (tính từ thời điểm dự kiến đi Macau) và 3 trang trắng",
            "Hộ chiếu cũ (nếu có)",
            "Ảnh mềm cỡ 4x6cm chụp không quá 6 tháng",
            "Căn cước công dân/Hộ khẩu/CT07/CT08",
            "Giấy đăng ký kết hôn (nếu đi cùng vợ/chồng)",
            "Giấy khai sinh các con (nếu đi cùng con cái)"
        ],
        "Giấy tờ công việc": [
            "Nếu là nhân viên: Xác nhận công việc, Đơn xin nghỉ phép",
            "Nếu là chủ doanh nghiệp: Đăng ký kinh doanh, Xác nhận nộp thuế 3 tháng gần nhất"
        ],
        "Giấy tờ chứng minh thu nhập": [
            "Sao kê tài khoản ngân hàng 3 tháng gần nhất",
            "Sổ tiết kiệm và xác nhận số dư sổ tiết kiệm có giá trị 4.000 USD"
        ]
    },
    "costs": {
        "options": [
            {"type": "Visa nhập cảnh 1 lần", "price": 300, "duration": "90 ngày"}
        ],
        "includes": [
            "Phí thị thực",
            "Phí dịch vụ của Passport Lounge"
        ],
        "excludes": [
            "Dịch vụ bổ sung hồ sơ tài chính & thu nhập"
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
    "terms": [
        "Phí dịch vụ, phí visa và các phí liên quan sẽ thanh toán 100% ngay khi ký hợp đồng.",
        "Passport Lounge không chịu trách nhiệm về quyết định từ chối visa.",
        "Không hoàn phí khi hồ sơ đã được nộp lên Đại Sứ Quán/Lãnh Sự Quán."
    ],
    "payment_methods": [
        {"name": "Chuyển khoản ngân hàng", "details": "CTY TNHH DU LỊCH VINHAROUND - Số TK: 0171003469686 - Vietcombank TPHCM"},
        {"name": "Thẻ tín dụng", "details": "Hỗ trợ trả góp 0% lãi suất"},
        {"name": "Ví MoMo", "details": "093-334-4646"}
    ],
    "created_at": datetime.now(),
    "updated_at": datetime.now()
}

#---------------------------------------------------------
#Visa Chau Au


# Chèn tất cả các dữ liệu visa vào database
visa_data = [china_visa, india_visa, taiwan_visa, korea_visa, hongkong_visa, russia_visa, japan_visa, macau_visa]
for visa in visa_data:
    db.insert_one("visas", visa)

print(f"Seeded data for {len(visa_data)} visas successfully!")