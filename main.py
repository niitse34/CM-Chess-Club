
import json
from datetime import datetime, timedelta
import os
from file_processing import FileProcessing, read_json, write_json

#classes
class Resource:
    def __init__(self,id,name,type):
        self.id = id
        self.name = name
        self.type = type
        
class Event:
    def __init__(self,id,name,type,start,end):
        self.id = id
        self.name = name
        self.type = type
        self.start = start
        self.end = end
        self.resources = []
        
    def add_resource(self,resource):
        self.resources.append(resource)
        
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "resources": [i.id for i in self.resources]
        }
        
class ChessClub:
    def __init__(self):
        self.resources = []
        self.events = []
        self.restrictions = []
        self.file_processing = FileProcessing(self)
        
    def search_resource(self, resource_id: str) -> "Resource | None":
        #search resource by id
        for resource in self.resources:
            if resource.id == resource_id:
                return resource
        return None
    
    def check_available(self, resource_id: str, start: datetime, end: datetime) -> bool:
        #check resource availability
        resource = self.search_resource(resource_id)
        if not resource:
            return False
        for event in self.events:
            if resource in event.resources:
                if not (end <= event.start or start >= event.end):
                    return False
        return True
    
    def load_initial_data(self):
        data = read_json("resources.json")
        if not data:
            return None
        for room in data.get("rooms", []):
            self.resources.append(Resource(room["id"], room["name"], "room"))
        for equip in data.get("equipment", []):
            self.resources.append(Resource(equip["id"], equip["name"], "equipment"))
        for person in data.get("staff", []):
            self.resources.append(Resource(person["id"], person["name"], "staff"))
        self.restrictions = data.get("restrictions", [])
        self.event_types = {type["id"]: type for type in data.get("event_types", [])}
        self.config = data.get("config",{})
        
    def validate_restrictions(self, event):
        #validate co-requirements and exclusions for an event
        for restriction in self.restrictions:
            if restriction["type"] == "co_requirement":
                if restriction.get("case") == event.type:
                    resources_event_ids = [i.id for i in event.resources]
                    requires = restriction.get("requires", [])
                    minimum_amount = restriction.get("min_amount", 1)
                    count = sum(1 for req in requires if req in resources_event_ids)
                    if count < minimum_amount:
                        missing = [r for r in requires if r not in resources_event_ids]
                        missing_ids = []
                        for r in missing:
                            res = self.search_resource(r)
                            missing_ids.append(res.name if res else r)
                        return False, f"Missing required resources for {event.type}: {', '.join(missing_ids)}"
        
        for restriction in self.restrictions:
            if restriction["type"] == "exclusion":
                affected_resources = restriction.get("resources", [])
                allowed_events = restriction.get("allowed_events", [])
                if any(r.id in affected_resources for r in event.resources):
                    if event.type not in allowed_events:
                        return False, restriction.get('name', 'Resource restriction failed')
        return True, "Valid"
        
    def schedule_event(self, name: str, type: str, start: datetime, end: datetime, resources_ids: list) -> tuple[bool, str]:
        #schedule new event
        if end <= start:
            return False, "Invalid time: end must be after start"
        
        #validate if event is scheduled for future date
        if start.date() <= datetime.now().date():
            return False, "Events can only be scheduled from tomorrow onwards"
        
        duration = (end-start).total_seconds() / 3600
        min_duration = self.config.get("min_duration", 0.5)
        max_duration = self.config.get("max_duration", 8.0)
        
        #check event type minimum duration
        if type in self.event_types:
            event_min = self.event_types[type].get("min_duration", 0)
            if duration < event_min:
                return False, f"{type} requires minimum {event_min}h duration"
        
        if duration < min_duration or duration > max_duration:
            return False, f"Duration must be {min_duration}-{max_duration}h"
        
        #validate opening and closing times only if existing in config
        if "opening_time" in self.config and "closing_time" in self.config:
            try:
                opening_time = self.config.get("opening_time")
                closing_time = self.config.get("closing_time")
                opening_hours, opening_mins = map(int, opening_time.split(":"))
                closing_hours, closing_mins = map(int, closing_time.split(":"))
                
                opening_dt = start.replace(hour=opening_hours, minute=opening_mins, second=0, microsecond=0)
                closing_dt = start.replace(hour=closing_hours, minute=closing_mins, second=0, microsecond=0)
                
                if start < opening_dt or end > closing_dt:
                    return False, f"Event must be within club hours ({opening_time}-{closing_time})"
            except (ValueError, AttributeError):
                return False, "Invalid time format in club configuration"
        
        temp = Event("temp", name, type, start, end)
        assigned_resources = []
        unavailable = []
        
        for resource_id in resources_ids:
            resource = self.search_resource(resource_id)
            if not resource:
                unavailable.append(f"{resource_id} (not found)")
                continue
            if not self.check_available(resource_id, start, end):
                unavailable.append(resource.name)
                continue
            assigned_resources.append(resource)
            temp.add_resource(resource)
        if unavailable:
            return False, "Unavailable or missing: " + ", ".join(unavailable)
        
        valid, message = self.validate_restrictions(temp)
        if not valid:
            return False, message
        
        event_id = f"event_{int(datetime.now().timestamp())}"
        event = Event(event_id, name, type, start, end)
        
        for resource in assigned_resources:
            event.add_resource(resource)
        self.events.append(event)
        return True, f"Scheduled: {name}"
    
    def find_next_slot(self, duration, resources_ids, event_type=""):
        #find next available time slot for given resources
        now = datetime.now()
        curr_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
        #get opening and closing times
        opening_time = self.config.get("opening_time", "00:00")
        closing_time = self.config.get("closing_time", "24:00")
        try:
            opening_hours, opening_mins = map(int, opening_time.split(":"))
            closing_hours, closing_mins = map(int, closing_time.split(":"))
        except (ValueError, AttributeError):
            return None
        
        for i in range(168):
            end_time = curr_time + timedelta(hours=duration)
            opening_dt = curr_time.replace(hour=opening_hours, minute=opening_mins, second=0, microsecond=0)
            closing_dt = curr_time.replace(hour=closing_hours, minute=closing_mins, second=0, microsecond=0)
            
            #check if slot is within club hours and resources are available
            
            if curr_time >= opening_dt and end_time <= closing_dt:
                if all(self.check_available(r, curr_time, end_time) for r in resources_ids):
                     #validate restrictions for potential event
                    
                    temp = Event("temp", "", event_type, curr_time, end_time)
                    for resource_id in resources_ids:
                        resource = self.search_resource(resource_id)
                        if resource:
                            temp.add_resource(resource)
                    valid, _ = self.validate_restrictions(temp)
                    if valid:
                        return curr_time
            curr_time += timedelta(hours=1)
        return None
        
    def delete_event(self, event_id: str) -> bool:
        """Delete an event by its ID."""
        for i, event in enumerate(self.events):
            if event.id == event_id:
                del self.events[i]
                return True
        return False
    
    def save_file(self, filename="CM_chess_club.json"):
        self.file_processing.save_file(filename)
        
    def load_file(self, filename="CM_chess_club.json"):
        self.file_processing.load_file(filename)

