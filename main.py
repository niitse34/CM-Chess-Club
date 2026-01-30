
import streamlit as st
import json
from datetime import datetime, timedelta
import os

def read_json(filename="resources.json"):
    dir = os.path.dirname(os.path.abspath(__file__))
    resource_path = os.path.join(dir, filename)
    try:
        with open(resource_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error(f"{filename} file not found")
        return None

def write_json(data, filename="resources.json"):
    dir = os.path.dirname(os.path.abspath(__file__))
    resource_path = os.path.join(dir, filename)
    with open(resource_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

st.set_page_config(page_title="Critical Mass Chess Club", layout="wide")
st.title("Critical Mass Chess Club")

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
        
        duration = (end-start).total_seconds() / 3600
        min_duration = self.config.get("min_duration", 0.5)
        max_duration = self.config.get("max_duration", 8.0)
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
    
    def find_next_slot(self, duration, resources_ids):
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
                    
                    temp = Event("temp", "", "", curr_time, end_time)
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
        data = {"events": [event.to_dict() for event in self.events]}
        dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        
    def load_file(self, filename="CM_chess_club.json"):
        dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(dir, filename)
        if not os.path.exists(path):
            return
        data = read_json(filename)
        if not data:
            return
        self.events = []
        for event_data in data.get("events", []):
            event = Event(event_data["id"], event_data["name"], event_data["type"],
                         datetime.fromisoformat(event_data["start"]),
                         datetime.fromisoformat(event_data["end"]))
            for resource_id in event_data.get("resources", []):
                resource = self.search_resource(resource_id)
                if resource:
                    event.add_resource(resource)
            self.events.append(event)

#initialize
if 'club' not in st.session_state:
    club = ChessClub()
    club.load_initial_data()
    club.load_file()
    st.session_state.club = club
else:
    club = st.session_state.club

#stats
col1, col2 = st.columns(2)
col1.write(f"Events: {len(club.events)}")
col2.write(f"Resources: {len(club.resources)}")

#navigation
page = st.selectbox("Menu", ["Events", "Add Event", "Find Slot", "Resources", "Save/Load"])

#events
if page == "Events":
    st.header("Events")
    if not club.events:
        st.write("No events")
    else:
        filter_date = st.date_input("Filter by date", value=None)
        events = club.events if not filter_date else [e for e in club.events if e.start.date() == filter_date]
        
        for event in sorted(events, key=lambda e: e.start):
            col1, col2, col3 = st.columns([2, 1, 1])
            col1.write(f"{event.name} ({event.type})")
            col2.write(f"{event.start.strftime('%m-%d %H:%M')}")
            col3.write(f"{len(event.resources)} res")
            if st.button("Delete", key=f"del_{event.id}"):
                club.delete_event(event.id)
                club.save_file()
                st.rerun()

#add event
elif page == "Add Event":
    st.header("Schedule Event")
    # Show scheduling message if present
    if "schedule_msg" in st.session_state:
        msg, msg_type = st.session_state.pop("schedule_msg")
        if msg_type == "success":
            st.success(msg)
        else:
            st.error(msg)
    name = st.text_input("Name")
    event_type = st.selectbox("Type", list(club.event_types.keys()) if club.event_types else [])
    tomorrow = datetime.now().date() + timedelta(days=1)
    date = st.date_input("Date", value=tomorrow)
    hour = st.number_input("Hour", 9, 20, 14)
    duration = st.number_input("Duration (h)", 0.5, 8.0, 2.0, step=0.5)
    
    st.write("Resources:")
    cols = st.columns(3)
    selected = []
    for i, r in enumerate(club.resources):
        with cols[i % 3]:
            if st.checkbox(r.name, key=f"res_{r.id}"):
                selected.append(r.id)
    
    if st.button("Schedule"):
        today = datetime.now().date()
        if not name or not event_type or not selected:
            st.session_state["schedule_msg"] = ("Fill missing fields", "error")
            st.rerun()
        elif date <= today:
            st.session_state["schedule_msg"] = ("events can only be scheduled from tomorrow", "error")
            st.rerun()
        else:
            start = datetime.combine(date, datetime.min.time().replace(hour=int(hour)))
            end = start + timedelta(hours=duration)
            ok, msg = club.schedule_event(name, event_type, start, end, selected)
            if ok:
                club.save_file()
                st.session_state["schedule_msg"] = (msg, "success")
                st.rerun()
            else:
                st.session_state["schedule_msg"] = (msg, "error")
                st.rerun()

#find slot
elif page == "Find Slot":
    st.header("Find Slot")
    duration = st.number_input("Duration (h)", 0.5, 8.0, 2.0, step=0.5)
    
    st.write("Resources:")
    cols = st.columns(3)
    selected = []
    for i, r in enumerate(club.resources):
        with cols[i % 3]:
            if st.checkbox(r.name, key=f"find_{r.id}"):
                selected.append(r.id)
    
    if st.button("Search"):
        if not selected:
            st.error("Select resources")
        else:
            slot = club.find_next_slot(duration, selected)
            if slot:
                end = slot + timedelta(hours=duration)
                st.success(f"{slot.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%H:%M')}")
            else:
                st.warning("No slot in next 7 days")

#resources
elif page == "Resources":
    st.header("Resources")
    for type_name in set([r.type for r in club.resources]):
        st.subheader(type_name)
        cols = st.columns(3)
        for i, r in enumerate([x for x in club.resources if x.type == type_name]):
            with cols[i % 3]:
                count = len([e for e in club.events if r in e.resources])
                st.write(f"{r.name}")
                st.caption(f"{count} events")

#save and load
elif page == "Save/Load":
    st.header("Save/Load")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save"):
            club.save_file()
            st.success("Saved")
    with col2:
        if st.button("Reload"):
            club.load_file()
            st.success("Reloaded")

