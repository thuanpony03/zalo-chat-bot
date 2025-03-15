# Service for managing customer leads
from datetime import datetime
from services.database import db
from models.lead import Lead
from bson import ObjectId

class LeadService:
    def __init__(self):
        self.collection = db.get_collection("leads")
        
    def create_lead(self, lead_data):
        """Create a new lead from data"""
        if isinstance(lead_data, dict):
            lead = Lead.from_dict(lead_data)
        elif isinstance(lead_data, Lead):
            lead = lead_data
        else:
            raise ValueError("lead_data must be a dict or Lead object")
            
        result = self.collection.insert_one(lead.to_dict())
        return str(result.inserted_id)
        
    def update_lead(self, lead_id, update_data):
        """Update an existing lead"""
        if isinstance(lead_id, str):
            lead_id = ObjectId(lead_id)
            
        update_data["updated_at"] = datetime.now()
        result = self.collection.update_one(
            {"_id": lead_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
        
    def add_note(self, lead_id, note_text, author=None):
        """Add a note to a lead"""
        if isinstance(lead_id, str):
            lead_id = ObjectId(lead_id)
            
        result = self.collection.update_one(
            {"_id": lead_id},
            {"$push": {
                "notes": {
                    "text": note_text,
                    "author": author,
                    "created_at": datetime.now()
                }
            }}
        )
        return result.modified_count > 0
        
    def assign_lead(self, lead_id, staff_id):
        """Assign a lead to a staff member"""
        if isinstance(lead_id, str):
            lead_id = ObjectId(lead_id)
            
        result = self.collection.update_one(
            {"_id": lead_id},
            {"$set": {
                "assigned_to": staff_id,
                "updated_at": datetime.now()
            }}
        )
        return result.modified_count > 0
        
    def set_follow_up(self, lead_id, follow_up_date):
        """Set a follow-up date for a lead"""
        if isinstance(lead_id, str):
            lead_id = ObjectId(lead_id)
            
        result = self.collection.update_one(
            {"_id": lead_id},
            {"$set": {
                "follow_up_date": follow_up_date,
                "updated_at": datetime.now()
            }}
        )
        return result.modified_count > 0
        
    def get_lead_by_phone(self, phone):
        """Get a lead by phone number"""
        data = self.collection.find_one({"phone": phone})
        return Lead.from_dict(data) if data else None
        
    def get_lead_by_id(self, lead_id):
        """Get a lead by ID"""
        if isinstance(lead_id, str):
            lead_id = ObjectId(lead_id)
            
        data = self.collection.find_one({"_id": lead_id})
        return Lead.from_dict(data) if data else None
        
    def get_leads_by_status(self, status, limit=100):
        """Get leads by status"""
        data = self.collection.find({"status": status}).sort("created_at", -1).limit(limit)
        return [Lead.from_dict(item) for item in data]
        
    def get_leads_for_staff(self, staff_id, limit=100):
        """Get leads assigned to a staff member"""
        data = self.collection.find({"assigned_to": staff_id}).sort("created_at", -1).limit(limit)
        return [Lead.from_dict(item) for item in data]
        
    def get_leads_to_follow_up_today(self):
        """Get leads that need to be followed up today"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59)
        
        data = self.collection.find({
            "follow_up_date": {
                "$gte": today_start,
                "$lte": today_end
            }
        }).sort("follow_up_date", 1)
        
        return [Lead.from_dict(item) for item in data]

# Initialize service
lead_service = LeadService()
