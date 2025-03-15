import pandas as pd
from datetime import datetime
from bson import ObjectId
from services.database import db

def import_excel_visa_products(excel_file_path):
    """Nhập dữ liệu visa từ file Excel vào MongoDB"""
    try:
        print(f"Bắt đầu nhập dữ liệu từ file {excel_file_path}")
        
        # Đọc file Excel
        df = pd.read_excel(excel_file_path)
        
        # Xác nhận số lượng sản phẩm đọc được
        product_count = len(df)
        print(f"Đọc được {product_count} sản phẩm từ file Excel")
        
        # Chuyển đổi dữ liệu để phù hợp với cấu trúc của collection visa
        visa_products = []

        #Xoa tat ca du lieu trong collection visa
        db.get_collection("visas").delete_many({})
        
        
        for index, row in df.iterrows():
            try:
                # Lấy thông tin cơ bản của sản phẩm - kiểm tra cả "Tên sản phẩm" và "Tên sản phẩm*"
                product_name = row.get('Tên sản phẩm*') or row.get('Tên sản phẩm', '')
                
                # Kiểm tra nếu tên sản phẩm trống
                if not product_name or str(product_name).strip() == '':
                    print(f"Bỏ qua dòng {index+2}: Tên sản phẩm trống")
                    continue
                    
                print(f"Đang xử lý sản phẩm: {product_name}")
                
                # Tách tên sản phẩm để lấy quốc gia
                # Ví dụ: "Visa Du Lịch Qatar" -> "Qatar"
                # Hoặc "Du Lịch Ả Rập Xê Út" -> "Ả Rập Xê Út"
                country_name = None
                
                # Xử lý trường hợp tên sản phẩm có "Visa"
                if "visa" in str(product_name).lower():
                    country_name = str(product_name).replace("Visa", "", 1).replace("visa", "", 1).replace("Du Lịch", "", 1).replace("du lịch", "", 1).strip()
                # Xử lý trường hợp tên sản phẩm có "Du Lịch"
                elif "du lịch" in str(product_name).lower():
                    country_name = str(product_name).replace("Du Lịch", "", 1).replace("du lịch", "", 1).strip()
                else:
                    # Trường hợp còn lại, lấy tên sản phẩm làm tên quốc gia
                    country_name = str(product_name).strip()
                
                if not country_name:
                    country_name = f"Visa_{index}"
                    print(f"Không thể trích xuất quốc gia từ '{product_name}'. Sử dụng tên mặc định: {country_name}")
                
                print(f"Tên quốc gia trích xuất: {country_name}")
                
                # Kiểm tra nếu đã có visa của quốc gia này
                existing_visa = db.get_collection("visas").find_one({"country": country_name})
                
                # Xác định loại visa từ thông tin sản phẩm
                visa_method = str(row.get('Nhãn hiệu', 'Visa điện tử'))  # Mặc định là visa điện tử
                visa_type = "du lịch"  # Mặc định là du lịch
                
                # Lấy giá từ sản phẩm
                price = row.get('Giá', 0)
                if isinstance(price, str):
                    price = float(price.replace('$', '').replace(',', '').strip()) if price else 0
                
                # Phân tích mô tả để trích xuất thông tin
                description = str(row.get('Mô tả sản phẩm', ''))
                short_desc = str(row.get('Mô tả ngắn', ''))
                
                # Tạo document visa mới
                visa_data = {
                    "_id": ObjectId(),
                    "country": country_name,
                    "country_aliases": [country_name.lower()],
                    "visa_type": visa_type,
                    "type_aliases": ["du lich", "du lịch", "tourist", "travel"],
                    "price": price,
                    "duration": "90 ngày",  # Mặc định
                    "processing_time": "5-7 ngày làm việc",  # Mặc định
                    "success_rate": 98.6,  # Mặc định
                    "visa_method": visa_method,
                    "requirements": extract_requirements(description),
                    "costs": extract_costs(description, price),
                    "process_steps": extract_process_steps(short_desc),
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "product_id": str(row.get('Id sản phẩm', '')),
                    "product_url": row.get('Đường dẫn/Alias', ''),
                    "description": description,  # Lưu cả mô tả gốc
                    "short_description": short_desc  # Lưu cả mô tả ngắn gốc
                }
                
                # In thông tin sản phẩm đã xử lý để kiểm tra
                print(f"Quốc gia: {visa_data['country']}, Giá: {visa_data['price']} USD")
                
                # Nếu đã tồn tại thì cập nhật, nếu không thì thêm mới
                if existing_visa:
                    print(f"Cập nhật visa cho quốc gia: {country_name}")
                    db.get_collection("visas").update_one(
                        {"_id": existing_visa["_id"]},
                        {"$set": visa_data}
                    )
                else:
                    print(f"Thêm visa mới cho quốc gia: {country_name}")
                    visa_products.append(visa_data)
                    
            except Exception as e:
                print(f"Lỗi khi xử lý dòng {index+2}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Thêm các visa mới vào database
        if visa_products:
            try:
                db.get_collection("visas").insert_many(visa_products)
                print(f"Đã nhập thành công {len(visa_products)} sản phẩm visa mới")
            except Exception as e:
                print(f"Lỗi khi thêm sản phẩm vào database: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("Không có sản phẩm mới để thêm vào database")
        
        return True
    except Exception as e:
        print(f"Lỗi tổng thể: {e}")
        import traceback
        traceback.print_exc()
        return False

def extract_requirements(description):
    """Trích xuất yêu cầu hồ sơ từ mô tả"""
    requirements = {}
    
    # Tìm phần "Hồ sơ xin visa" trong mô tả
    if "Hồ sơ xin visa" in description or "Hồ sơ" in description:
        # Tìm các mục theo định dạng <strong>Hồ sơ cá nhân</strong>
        sections = ["Hồ sơ cá nhân", "Hồ sơ chứng minh công việc", "Hồ sơ chứng minh tài chính"]
        
        for section in sections:
            if section in description:
                start_idx = description.find(section)
                if start_idx != -1:
                    # Tìm phần tiếp theo của li tags
                    docs = []
                    # Phân tích các mục trong danh sách
                    lines = description[start_idx:].split('<li>')
                    for line in lines[1:10]:  # Giới hạn 10 mục đầu tiên
                        if '</li>' in line:
                            doc = line.split('</li>')[0].strip()
                            if doc:
                                docs.append(doc)
                    
                    if docs:
                        category = section.replace("Hồ sơ", "").strip()
                        requirements[category] = docs
    
    return requirements or {"Giấy tờ cần thiết": ["Hộ chiếu còn hạn ít nhất 6 tháng", "Ảnh thẻ 4x6 nền trắng"]}

def extract_costs(description, default_price):
    """Trích xuất thông tin chi phí từ mô tả"""
    costs = {
        "options": [],
        "includes": [],
        "excludes": []
    }
    
    # Tìm bảng chi phí
    if "Chi phí xin visa" in description and "USD" in description:
        # Cố gắng trích xuất các option từ bảng
        lines = description.split('<tr')
        for line in lines:
            if '<td' in line and 'USD' in line:
                # Tìm tên loại visa
                visa_type = ""
                duration = "90 ngày"
                price = default_price
                
                if "Visa nhập cảnh 1 lần" in line:
                    visa_type = "Visa nhập cảnh 1 lần"
                elif "Visa nhập cảnh nhiều lần" in line:
                    visa_type = "Visa nhập cảnh nhiều lần" 
                    duration = "1 năm"
                elif "Evisa" in line:
                    visa_type = "eVisa"
                
                # Trích xuất giá
                if "USD" in line:
                    price_str = line.split("USD")[0].strip()
                    price_str = ''.join(filter(str.isdigit, price_str[-5:]))
                    if price_str:
                        price = float(price_str)
                
                if visa_type:
                    costs["options"].append({
                        "type": visa_type,
                        "price": price,
                        "duration": duration
                    })
    
    # Nếu không tìm thấy option nào, thêm mặc định
    if not costs["options"]:
        costs["options"].append({
            "type": "Visa du lịch tiêu chuẩn",
            "price": default_price,
            "duration": "90 ngày"
        })
    
    # Trích xuất thông tin chi phí bao gồm
    if "Chi phí bao gồm:" in description:
        includes_section = description.split("Chi phí bao gồm:")[1].split("Không bao gồm")[0]
        includes = [line.strip() for line in includes_section.replace("<br>", "\n").split("\n") if line.strip()]
        costs["includes"] = includes[:5]  # Giới hạn 5 mục
    
    # Trích xuất thông tin chi phí không bao gồm
    if "Không bao gồm:" in description:
        excludes_section = description.split("Không bao gồm:")[1].split("<p>")[0]
        excludes = [line.strip() for line in excludes_section.replace("<br>", "\n").split("\n") if line.strip()]
        costs["excludes"] = excludes[:3]  # Giới hạn 3 mục
    
    return costs

def extract_process_steps(short_desc):
    """Trích xuất các bước xử lý từ mô tả ngắn"""
    process_steps = []
    
    if short_desc:
        steps = short_desc.replace("<p>", "").replace("</p>", "").split("<br>")
        for step in steps:
            step = step.strip()
            if step and ")" not in step and step != "Gọi ngay":
                name = step.split("(")[0].strip()
                description = ""
                if "(" in step and ")" in step:
                    description = step.split("(")[1].split(")")[0].strip()
                
                if name:
                    process_steps.append({
                        "name": name,
                        "description": description
                    })
    
    # Nếu không tìm thấy bước nào, thêm các bước mặc định
    if not process_steps:
        process_steps = [
            {"name": "Đăng ký tư vấn", "description": "10 phút trao đổi thông tin"},
            {"name": "Hoàn tất hồ sơ", "description": "1-2 ngày làm việc"},
            {"name": "Đặt lịch hẹn", "description": "Đặt lịch nộp hồ sơ"},
            {"name": "Nhận kết quả", "description": "Thông báo và giao kết quả"}
        ]
    
    return process_steps

if __name__ == "__main__":
    # Đường dẫn đến file Excel - điều chỉnh cho phù hợp
    excel_file_path = "visa_products.xlsx"
    import_excel_visa_products(excel_file_path)