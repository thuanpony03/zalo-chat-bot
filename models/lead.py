# Model for lead management
from datetime import datetime
from bson import ObjectId
from .base import BaseModel

class Lead(BaseModel):
    def __init__(self, name=None, phone=None, email=None, country_interest=None, 
                 zalo_user_id=None, source="zalo_bot", status="new_lead",
                 customer_needs=None, special_concerns=False, special_case_type=None,
                 original_query=None, description=None):
        super().__init__()
        self.name = name
        self.phone = phone
        self.email = email
        self.country_interest = country_interest
        self.zalo_user_id = zalo_user_id
        self.source = source
        self.status = status  # new_lead, contacted, qualified, converted, rejected
        self.customer_needs = customer_needs or []
        self.special_concerns = special_concerns
        self.special_case_type = special_case_type
        self.original_query = original_query
        self.description = description  # Add this line
        self.assigned_to = None
        self.notes = []
        self.last_contact_date = None
        self.follow_up_date = None
        
    def add_note(self, note_text, author=None):
        """Add a note to this lead"""
        self.notes.append({
            "text": note_text,
            "author": author,
            "created_at": datetime.now()
        })
        
    def to_dict(self):
        result = super().to_dict()
        return result

    @staticmethod
    def from_dict(data):
        lead = Lead(
            name=data.get("name"),
            phone=data.get("phone"),
            email=data.get("email"),
            country_interest=data.get("country_interest"),
            zalo_user_id=data.get("zalo_user_id"),
            source=data.get("source", "zalo_bot"),
            status=data.get("status", "new_lead"),
            customer_needs=data.get("customer_needs", []),
            special_concerns=data.get("special_concerns", False),
            special_case_type=data.get("special_case_type"),
            original_query=data.get("original_query"),
            description=data.get("description")  # Add this line
        )
        
        lead._id = data.get("_id", ObjectId())
        lead.created_at = data.get("created_at", datetime.now())
        lead.updated_at = data.get("updated_at", datetime.now())
        lead.assigned_to = data.get("assigned_to")
        lead.notes = data.get("notes", [])
        lead.last_contact_date = data.get("last_contact_date")
        lead.follow_up_date = data.get("follow_up_date")
        
        return lead
