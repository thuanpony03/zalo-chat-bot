from models.visa import Visa
from services.database import db

def init_visa_data():
    db.drop_collection("visas")
    
    china_visa = Visa(
        country="Trung Quốc",
        visa_type="du lịch",
        price=180,
        duration="90 ngày",
        processing_time="10-15 ngày làm việc",
        success_rate=98.6
    )
    china_visa.add_alias(country_alias="trung quoc")
    china_visa.add_alias(country_alias="trung quốc")
    china_visa.add_alias(country_alias="china")
    china_visa.add_alias(country_alias="tq")
    china_visa.add_alias(country_alias="trung")
    china_visa.add_alias(country_alias="trung hoa")
    china_visa.add_alias(type_alias="du lich")
    china_visa.add_alias(type_alias="du lịch")
    china_visa.add_alias(type_alias="tourist")
    china_visa.add_requirement("travel_docs", [
        "Hộ chiếu gốc còn hạn ít nhất 6 tháng",
        "Ảnh thẻ 4x6cm nền trắng chụp trong vòng 3 tháng",
        "Bản scan CCCD/CMND",
        "Đơn xin visa điền đầy đủ thông tin",
        "Giấy xác nhận thông tin cư trú – Mẫu CT07 hoặc Sổ hộ khẩu bản photo"
    ])
    china_visa.add_requirement("financial_docs", [
        "Sao kê tài khoản ngân hàng 3 tháng gần nhất",
        "Giấy tờ chứng minh công việc và thu nhập"
    ])
    china_visa.add_requirement("family_docs", [
        "Giấy đăng ký kết hôn (nếu đi cùng vợ/chồng)",
        "Giấy khai sinh (nếu đi cùng con)",
        "Giấy ủy quyền của cha mẹ (nếu trẻ em đi cùng 1 trong 2 người)"
    ])
    china_visa.add_cost_option("Visa nhập cảnh 1 lần", 180, "90 ngày")
    china_visa.add_cost_option("Visa nhập cảnh nhiều lần", 300, "1 năm")
    china_visa.add_cost_detail(includes="Phí lãnh sự quán")
    china_visa.add_cost_detail(includes="Phí dịch vụ của Passport Lounge")
    china_visa.add_cost_detail(excludes="Phí bổ sung hồ sơ tài chính")
    china_visa.add_cost_detail(excludes="Phí xử lý nhanh")

    db.insert_one("visas", china_visa.to_dict())
    print("Đã tạo dữ liệu visa Trung Quốc thành công!")