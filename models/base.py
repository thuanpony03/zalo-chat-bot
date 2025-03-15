from datetime import datetime
from bson import ObjectId

class BaseModel:
    def __init__(self):
        self._id = ObjectId()
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self):
        return self.__dict__