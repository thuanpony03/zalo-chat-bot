import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.visa_service import visa_service

def test_special_case_detection():
    """Test the detection of special cases in visa queries"""
    
    test_cases = [
        # Test cases for no savings
        {"query": "Em ơi, chị không có sổ tiết kiệm thì sao đi xin visa được đây em", "expected": "no_savings"},
        {"query": "Tôi chưa có sổ tiết kiệm, có xin được visa không?", "expected": "no_savings"},
        {"query": "Không đủ tiền trong sổ thì sao?", "expected": "no_savings"},
        
        # Test cases for freelance jobs
        {"query": "Em ơi, chị công việc tự do thì sao đi xin visa được đây em", "expected": "freelance_job"},
        {"query": "Tôi làm freelance thì xin visa được không?", "expected": "freelance_job"},
        {"query": "Tôi kinh doanh tự do không có công ty", "expected": "freelance_job"},
        
        # Test cases for illegal stay
        {"query": "Em ơi, chồng chị ở bất hợp pháp bên Canada thì chị có xin được visa qua thăm chồng không em", "expected": "illegal_stay"},
        {"query": "Em ơi, chị ở bất hợp pháp bên Đài Loan bây giờ chị xin visa du lịch qua đi chơi được không?", "expected": "illegal_stay"},
        {"query": "Người nhà tôi đang xin tị nạn ở Mỹ", "expected": "illegal_stay"},
        
        # Test cases for tax issues
        {"query": "Em ơi, chị muốn đi Châu Âu mà không đóng thuế thì có thể đậu visa không em", "expected": "tax_issues"},
        {"query": "Tôi không kê khai thuế, có xin được visa không?", "expected": "tax_issues"},
        {"query": "Tôi thiếu thuế mấy năm nay", "expected": "tax_issues"},
        
        # Test cases for no bank statement
        {"query": "Em ơi, chị muốn đi Châu Âu mà không sao kê xin visa đậu không em", "expected": "no_bank_statement"},
        {"query": "Xin visa mà không có giấy sao kê thì sao?", "expected": "no_bank_statement"},
        {"query": "Tôi không có bảng lương", "expected": "no_bank_statement"},
        
        # Test cases for proof requests
        {"query": "Em ơi, bên em có chứng minh công việc và tài chính không em", "expected": "proof_request"},
        {"query": "Bên anh có hỗ trợ chứng minh tài chính không?", "expected": "proof_request"},
        {"query": "Giúp tôi làm hồ sơ được không?", "expected": "proof_request"},
        
        # Test cases for previous rejection
        {"query": "Tôi đã từng bị từ chối visa Mỹ", "expected": "previous_rejection"},
        {"query": "Tôi bị trượt visa Úc năm ngoái", "expected": "previous_rejection"},
        
        # Test cases for family travel
        {"query": "Tôi muốn đi cùng gia đình, vợ và 2 con", "expected": "travel_with_family"},
        {"query": "Xin visa đi du lịch cùng vợ", "expected": "travel_with_family"},
        
        # Test cases for normal queries
        {"query": "Làm visa Nhật mất bao lâu?", "expected": None},
        {"query": "Chi phí visa Hàn Quốc là bao nhiêu?", "expected": None},
    ]
    
    for i, test_case in enumerate(test_cases):
        query = test_case["query"]
        expected = test_case["expected"]
        result = visa_service.detect_special_case_query(query)
        
        if result == expected:
            print(f"✅ Test case {i+1} passed: '{query}' -> {result}")
        else:
            print(f"❌ Test case {i+1} failed: '{query}' -> Expected: {expected}, Got: {result}")

if __name__ == "__main__":
    print("Testing special case detection...")
    test_special_case_detection()
