def get_special_case_template(case_type="general", country=None):
    """Trả về template phù hợp với loại trường hợp đặc biệt"""
    
    templates = {
        "financial": f"""
Chào bạn,

Tôi hiểu nỗi lo của bạn về vấn đề chứng minh tài chính khi xin visa {country or ''}. Đây là tình huống mà nhiều khách hàng của Passport Lounge cũng từng gặp phải.

Với kinh nghiệm lâu năm, đội ngũ chuyên viên visa của chúng tôi đã hỗ trợ thành công nhiều trường hợp tương tự. Mỗi hồ sơ có những đặc thù riêng và cần được phân tích kỹ lưỡng để tìm ra phương án tối ưu.

Thay vì trao đổi qua tin nhắn, bạn vui lòng gọi ngay hotline 1900 636563 để được chuyên viên giàu kinh nghiệm tư vấn chi tiết. Họ sẽ đánh giá tình hình và đề xuất các giải pháp phù hợp, giúp bạn nâng cao đáng kể cơ hội đậu visa.

Passport Lounge rất mong được hỗ trợ bạn sớm nhất!
        """,
        
        "job": f"""
Chào bạn,

Tôi hoàn toàn thấu hiểu băn khoăn của bạn về việc chứng minh công việc khi xin visa {country or ''}. Đây là vấn đề mà nhiều khách hàng của Passport Lounge cũng từng đối mặt.

Với hơn 10 năm kinh nghiệm, đội ngũ tư vấn visa của chúng tôi đã hỗ trợ thành công nhiều trường hợp có công việc tự do hoặc khó chứng minh thu nhập. Mỗi hồ sơ đều cần được phân tích riêng để tìm ra giải pháp phù hợp nhất.

Thay vì trò chuyện qua tin nhắn, bạn vui lòng gọi ngay hotline 1900 636563 để được chuyên viên visa giàu kinh nghiệm tư vấn chi tiết. Họ sẽ đánh giá tình hình của bạn và đề xuất phương án tối ưu, giúp bạn nâng cao cơ hội đậu visa.

Passport Lounge rất mong được hỗ trợ bạn sớm nhất có thể!
        """,
        
        "rejection": f"""
Chào bạn,

Tôi hiểu rằng việc từng bị từ chối visa có thể gây lo lắng khi bạn muốn xin visa {country or ''} lần này. Đây là tình huống mà nhiều khách hàng của Passport Lounge đã trải qua và vượt qua thành công.

Với kinh nghiệm lâu năm trong ngành, chúng tôi đã giúp nhiều khách hàng thành công trong lần nộp hồ sơ tiếp theo bằng cách phân tích kỹ lưỡng nguyên nhân từ chối trước đó và xây dựng chiến lược khắc phục hiệu quả.

Thay vì trao đổi qua tin nhắn, bạn vui lòng gọi ngay hotline 1900 636563 để được chuyên viên visa giàu kinh nghiệm tư vấn chi tiết. Họ sẽ đánh giá tình hình của bạn và đưa ra giải pháp phù hợp nhất.

Passport Lounge rất mong được đồng hành cùng bạn!
        """,
        
        "general": f"""
Chào bạn,
x`
Tôi hiểu những băn khoăn mà bạn đang gặp phải khi xin visa {country or ''}. Đây là tình huống mà nhiều khách hàng của Passport Lounge cũng từng trải qua.

Với hơn 10 năm kinh nghiệm, đội ngũ tư vấn visa của chúng tôi đã hỗ trợ thành công rất nhiều trường hợp tương tự. Mỗi hồ sơ visa đều có những đặc thù riêng và cần được phân tích cụ thể để tìm giải pháp phù hợp nhất.

Thay vì trao đổi qua tin nhắn, bạn vui lòng gọi ngay hotline 1900 636563 để được chuyên viên visa giàu kinh nghiệm của chúng tôi tư vấn chi tiết. Họ sẽ đánh giá tình hình của bạn và đề xuất phương án tối ưu, giúp bạn nâng cao đáng kể cơ hội đậu visa.

Passport Lounge rất mong được hỗ trợ bạn sớm nhất có thể!
        """
    }
    
    return templates.get(case_type, templates["general"]).strip()