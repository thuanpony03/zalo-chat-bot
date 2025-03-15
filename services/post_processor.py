"""
Post-processing for AI-generated responses
"""
import re
import random

class ResponsePostProcessor:
    """Process responses to ensure they're concise and appropriate"""
    
    @staticmethod
    def ensure_concise(response, max_length=1500):
        """Ensure response is concise"""
        # If already short enough, return as is
        if len(response) <= max_length:
            return response
            
        # Truncate to sentences that fit within max length
        sentences = re.split(r'(?<=[.!?])\s+', response)
        result = ""
        
        for sentence in sentences:
            if len(result + sentence) > max_length - 100:  # Leave room for call to action
                break
            result += sentence + " "
        
        # Increase likelihood of adding contact information if not already present - from 15% to 30%
        contact_info_present = any(phrase in result.lower() for phrase in ["hotline", "1900", "liên hệ", "gọi", "để lại số", "điện thoại"])
        
        if not contact_info_present and random.random() < 0.30:  # Increased from 15% to 30%
            # For truly complex queries, suggest the hotline
            complex_topics = ["hồ sơ đặc biệt", "trường hợp phức tạp", "bị từ chối", "trượt visa", "tài chính", "công việc", "sổ tiết kiệm"]
            if any(topic in result.lower() for topic in complex_topics):
                contact_options = [
                    " Nếu anh/chị cần tư vấn chi tiết hơn, có thể gọi hotline 1900 636563 của Passport Lounge ạ.",
                    " Anh/chị có thể để lại số điện thoại để chuyên viên của Passport Lounge tư vấn chi tiết hơn ạ.",
                    " Anh/chị vui lòng liên hệ hotline 1900 636563 để được tư vấn cụ thể hơn về trường hợp này ạ."
                ]
                result += random.choice(contact_options)
            else:
                general_contact = [
                    " Nếu anh/chị muốn được tư vấn nhanh hơn, có thể để lại số điện thoại hoặc gọi 1900 636563 ạ.",
                    " Anh/chị có thể gọi hotline 1900 636563 để được hỗ trợ trực tiếp ạ.",
                    " Để tiện trao đổi chi tiết hơn, anh/chị có thể để lại số điện thoại hoặc liên hệ hotline 1900 636563 ạ."
                ]
                result += random.choice(general_contact)
            
        # Add a question at the end if not already present to create natural conversation flow
        has_question = any(phrase in result.lower() for phrase in ["còn gì", "thắc mắc", "cần tư vấn", "cần hỗ trợ", "?"])
        if not has_question and not result.strip().endswith("?"):
            question_options = [
                " Anh/chị còn câu hỏi nào khác không ạ?", 
                " Anh/chị có thắc mắc gì thêm không ạ?",
                " Còn vấn đề nào anh/chị quan tâm nữa không ạ?"
            ]
            result += random.choice(question_options)
            
        return result
            
    @staticmethod
    def add_quick_reply_suggestion(response):
        """Add suggestion for quick reply if not present"""
        # Check if response already has a question to engage the user
        has_question = any(phrase in response.lower() for phrase in ["còn gì", "thắc mắc", "cần tư vấn", "cần hỗ trợ", "?"])
        
        # Check if response contains pricing information
        has_price_info = any(term in response.lower() for term in ["giá", "chi phí", "vnđ", "đồng", "phí", "triệu"])
        has_contact_info = any(phrase in response.lower() for phrase in ["hotline", "1900", "liên hệ", "gọi", "để lại số", "điện thoại", "sđt"])
        
        # Only add contact info for short responses and only if not already present
        if len(response) < 300 and not has_contact_info and not has_question:
            if has_price_info and random.random() < 0.4:  # Increased from 20% to 40%
                # For price-related responses, sometimes suggest leaving a phone number
                contact_patterns = [
                    "Anh/chị quan tâm đến mức giá cụ thể có thể để lại SĐT hoặc gọi hotline 1900 636563 ạ.",
                    "Nếu muốn biết chi phí chính xác nhất, anh/chị có thể liên hệ hotline 1900 636563 ạ.",
                    "Để có báo giá chi tiết nhất cho trường hợp của anh/chị, vui lòng để lại số điện thoại hoặc gọi 1900 636563 ạ.",
                    "Anh/chị vui lòng để lại số điện thoại hoặc gọi 1900 636563 để được tư vấn chi phí chi tiết nhất ạ."
                ]
                response += " " + random.choice(contact_patterns)
            elif random.random() < 0.25:  # Increased from 10% to 25%
                # Add a question at the end or contact suggestion
                if random.random() < 0.6:  # 60% chance to add contact info
                    contact_options = [
                        "Anh/chị có thể để lại SĐT hoặc gọi 1900 636563 để được hỗ trợ chi tiết hơn ạ.",
                        "Để được hỗ trợ nhanh nhất, anh/chị có thể gọi hotline 1900 636563 ạ.",
                        "Anh/chị vui lòng để lại số điện thoại để chuyên viên tư vấn sẽ liên hệ ngay ạ."
                    ]
                    response += " " + random.choice(contact_options)
                else:
                    question_options = [
                        "Anh/chị còn câu hỏi gì nữa không ạ?", 
                        "Anh/chị cần hỗ trợ thêm vấn đề gì không ạ?",
                        "Còn điều gì anh/chị muốn biết thêm không ạ?"
                    ]
                    response += " " + random.choice(question_options)
        
        return response
    
    @staticmethod
    def process(response):
        """Apply all post-processing steps"""
        # Ensure minimum desired length (~300 chars)
        if len(response) < 200:
            response = ResponsePostProcessor.add_quick_reply_suggestion(response)
            
        # Ensure maximum length
        response = ResponsePostProcessor.ensure_concise(response, 500)
        
        return response

post_processor = ResponsePostProcessor()
