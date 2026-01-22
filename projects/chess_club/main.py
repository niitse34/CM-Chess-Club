import streamlit as st
import json
from datetime import datetime, timedelta
import os
from functions import read_json,write_json

read_json()

st.set_page_config(
    page_title = "Critical Mass Chess Club"
)

#Main Title
st.title("Critical Mass Chess Club")

#Classes

class Resource:
    def __init__(self,id,name,type,available=True):
        self.id = id
        self.name = name
        self.type = type
        self.available = available
        self.scheduled_events = []
        
class Event:
    def __init__(self,id,name,type,start,end):
        self.id = id
        self.name = name
        self.type = type
        self.start = start
        self.end = end
        self.resources = []
        self.state = "scheduled"
        
    def add_resource(self,resource):
        self.resources.append(resource)
        
    def collides_with(self,ot_event):
        return (self.start < ot_event.end and self.end > ot_event.start)
        
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "resources": [i.id for i in self.resources],
            "state": self.state
        }
        
class ChessClub:
    def __init__(self):
        self.resources = []
        self.events = []
        self.restrictions = []
        
    def search_resource(self,resource_id):
        for resource in self.resources:
            if resource.id == resource_id:
                return resource
    def check_available(self,resource_id,start,end):
        resource = self.search_resource(resource_id)
        if not resource:
            return False
        for event in self.events:
            if resource in event.resources:
                if not (end <= event.start or start >= event.end):
                    return False
        return True
    
    def get_event_start(self,event):
        return event.start
    
    
    #load data from resources.json
    def load_initial_data(self):
        dir = os.path.dirname(os.path.abspath(__file__))
        resource_path = os.path.join(dir, "resources.json")
        try:
            with open(resource_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            st.error(f"resources.json file not found")
            return None
        #rooms
        for room in data.get("rooms", []):
            self.resources.append(Resource(
                id=room["id"],
                name=room["name"],
                type="room",
                available=True
            ))
        #equipment
        for equip in data.get("equipment", []):
            self.resources.append(Resource(
                id = equip["id"],
                name = equip["name"],
                type="equipment",
                available=True
            ))
        #staff
        for person in data.get("staff", []):
            self.resources.append(Resource(
                id = person["id"],
                name = person["name"],
                type="staff",
                available=True
            ))
        #load restrictions from json
        self.restrictions = data.get("restrictions", [])
        
        #
        #
        #
        #
        #
        #pendiente
        #
        #
        #
        #
        #
        
        def validate_restrictions(self,event):
            #check mutual requirements
            for restriction in self.restrictions:
                if restriction["type"] == "mut_requirement":
                    #check if restriction applies
                    if restriction.get("case") == event.type:
                        resources_event_ids = [i.id for i in event.resources]
                        requires = restriction.get("requires", [])
                        minimum_amount = restriction.get("minimum_amount",1)
                        
                        if event.type == "match":
                            has_board = any(r.startswith("board_") for r in resources_event_ids)
                            has_pieces = any(r.startswith("pieces_") for r in resources_event_ids)
                            if not (has_board and has_pieces):
                                return False, "missing board and/or pieces for the match"
            #check exclusions
            for restriction in self.restrictions:
                if restriction["type"] == "exclusion":
                    affected_resources = restriction.get("resources", [])
                    allowed_events = restriction.get("allowed_events", [])
                    
                    #if event uses affected resources and is not in allowed events
                    if any(r.id in affected_resources for r in event.resources):
                        if event.type not in allowed_events:
                            return False, f"restricted resource"
            return True
        
        def plan_event(self,name,type,start,end,resources_ids):
            #check valid duration
            if end <= start:
                return False, "end time must be after start time"
            
            #calculate duration (hours)
            duration = (end-start).total_seconds() / 3600
            
            #validate min and max durations
            
            min_duration = self.config.get("min_duration", 0.5)
            max_duration = self.config.get("max_duration", 8.0)
            if duration < min_duration or duration > max_duration:
              return False, f"duration must be between {min_duration} and {max_duration} hours"
          
            #event type validation
            
            if type in self.event_type:
                expected_duration = self.event_type[type].get("duration", 0)
                if expected_duration > 0 and duration < expected_duration:
                    return False, f"{type} type requires at least {expected_duration} hours"
                
            #validations event
            
            val_event = Event("val", name, type, start, end)
            
            #check availability
            assigned_resources = []
            for resource_id in resources_ids:
                if not self.check_available(resource_id,start,end):
                    resource = self.search_resource(resource_id)
                    return False,f"resource {resource.id} not available"
                resource = self.search_resource(resource_id),
                if resource:
                    assigned_resources.append(resource)
                    val_event.add_resource(resource)
                    
            #validate restrictions
            
            valid, message = self.validate_restrictions(val_event)
            if not valid:
                return False, message
            
            #create event
            
            event_id = f"event" #########
            event = Event(event_id, name, type, start, end)
            for resource in assigned_resources:
                event.add_resource(resource)
                
            self.events.append(event)
            return True, f"{name} event successfully scheduled"
        
        def search_next_space(self,duration,resources_ids):
            now = datetime.now()
            
            #start next hour
            curr_time = now.replace(minute=0,second=0,microsecond=0) + timedelta(hours=1)
            
            #search in following 7 days
            for i in range(168): #7 days in hours
                recom_end = curr_time + timedelta(hours=duration)
                
                #verify availability for every resource
                all_available = all(
                    self.check_available(r,curr_time,recom_end)
                    for r in resources_ids
                )
                
                if all_available:
                    return curr_time
                curr_time += timedelta(hours=1)
                
        def delete_event(self, event_id):
            for i, event in enumerate(self.events):
                if event.id == event_id:
                    del self.events[i]
                    return True
                return False
        
        def save_file(self,filename="CM_chess_club.json"):
            data = {
                "events"
            }
        pass
    
    #######################
    
    
          