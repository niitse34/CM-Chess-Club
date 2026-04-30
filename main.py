
import json
from datetime import datetime, timedelta
import os
from file_processing import FileProcessing, read_json, write_json
from models import Resource, Event

class ChessClub:
    def __init__(self):
        self.resources = []
        self.events = []
        self.restrictions = []
        self.file_processing = FileProcessing(self)
        #spare pieces policy defaults
        self.spare_per_day = 50
        self.spare_per_event = 10
        
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
            self.resources.append(Resource(equip["id"], equip["name"], equip.get("type", "equipment")))
        for person in data.get("staff", []):
            self.resources.append(Resource(person["id"], person["name"], person.get("type", "staff")))
        self.restrictions = data.get("restrictions", [])
        self.event_types = {type["id"]: type for type in data.get("event_types", [])}
        self.config = data.get("config",{})
        #load spare piece policy from config if present
        try:
            self.spare_per_day = int(self.config.get("spare_per_day", self.spare_per_day))
        except (TypeError, ValueError):
            self.spare_per_day = 50
        try:
            self.spare_per_event = int(self.config.get("spare_per_event", self.spare_per_event))
        except (TypeError, ValueError):
            self.spare_per_event = 10
        
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
        
    def schedule_event(self, name: str, type: str, start: datetime, end: datetime, resources_ids: list, spare_pieces = None) -> tuple[bool, str]:
        #schedule new event
        if end <= start:
            return False, "Invalid time: end must be after start"
        
        #validate if event is scheduled for future date
        if start.date() <= datetime.now().date():
            return False, "Events can only be scheduled from tomorrow onwards"
        
        #check if event is scheduled on a blocked day
        blocked_days = self.config.get("blocked_days", [])
        if blocked_days:
            day_name = start.strftime("%A") #get day name from date
            if day_name in blocked_days:
                return False, f"Events cannot be scheduled on {day_name}s"
        
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

        #check spare pieces pool for event date
        try:
            event_date = start.date()
            existing_events_same_date = [e for e in self.events if e.start.date() == event_date]
            # use per-event spare_pieces if provided, otherwise use global default
            spares_for_this_event = spare_pieces if spare_pieces is not None else self.spare_per_event
            total_needed = sum(e.spare_pieces if e.spare_pieces is not None else self.spare_per_event for e in existing_events_same_date) + spares_for_this_event
            if total_needed > self.spare_per_day:
                return False, f"Not enough spare pieces for {event_date}: {self.spare_per_day} available, {total_needed} needed ({spares_for_this_event} for this event)"
        except Exception:
            pass
        
        event_id = f"event_{int(datetime.now().timestamp())}"
        event = Event(event_id, name, type, start, end, spare_pieces=spare_pieces)
        
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
        blocked_days = self.config.get("blocked_days", [])
        try:
            opening_hours, opening_mins = map(int, opening_time.split(":"))
            closing_hours, closing_mins = map(int, closing_time.split(":"))
        except (ValueError, AttributeError):
            return None
        
        for i in range(168): #7 days
            #skip blocked days
            day_name = curr_time.strftime("%A")
            if day_name in blocked_days:
                curr_time += timedelta(hours=1)
                continue
            
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
    
    def get_coach_workload(self, coach_id: str) -> float:
        #calculate total hours of events for a coach in the next 7 days
        now = datetime.now()
        week_from_now = now + timedelta(hours=168)
        total_hours = 0.0
        
        for event in self.events:
            if event.start >= now and event.start < week_from_now:
                #check if coach is in this events resources
                if any(r.id == coach_id for r in event.resources):
                    duration = (event.end - event.start).total_seconds() / 3600
                    total_hours += duration
        
        return total_hours
    
    def get_available_coaches(self) -> list:
        #get all coaches resources
        coach_ids = ["fm", "im", "gm"]
        return [self.search_resource(cid) for cid in coach_ids if self.search_resource(cid)]
    
    def suggest_alternative_coach(self, busy_coach_id: str) -> "Resource | None":
        #suggest less busy coach alternative
        coaches = self.get_available_coaches()
        if not coaches or len(coaches) < 2:
            return None
        
        #find coach with least workload in next 7 days
        least_busy = min(coaches, key=lambda c: self.get_coach_workload(c.id))
        
        #only suggest if least_busy is actually less busy
        if self.get_coach_workload(least_busy.id) < self.get_coach_workload(busy_coach_id):
            return least_busy
        return None
    
    def save_file(self, filename="CM_chess_club.json"):
        self.file_processing.save_file(filename)
        
    def load_file(self, filename="CM_chess_club.json"):
        self.file_processing.load_file(filename)

