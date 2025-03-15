from .base import BaseModel

class Visa(BaseModel):
    def __init__(self, country, visa_type, price, duration, processing_time, success_rate=None):
        super().__init__()
        self.country = country
        self.country_aliases = []
        self.visa_type = visa_type
        self.type_aliases = []
        self.price = price
        self.duration = duration
        self.processing_time = processing_time
        self.success_rate = success_rate
        self.requirements = {}
        self.costs = {"options": [], "includes": [], "excludes": []}

    def add_alias(self, country_alias=None, type_alias=None):
        if country_alias:
            self.country_aliases.append(country_alias)
        if type_alias:
            self.type_aliases.append(type_alias)

    def add_requirement(self, category, documents):
        self.requirements[category] = documents

    def add_cost_option(self, type, price, duration):
        self.costs["options"].append({"type": type, "price": price, "duration": duration})

    def add_cost_detail(self, includes=None, excludes=None):
        if includes:
            self.costs["includes"].append(includes)
        if excludes:
            self.costs["excludes"].append(excludes)