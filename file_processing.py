import json
from datetime import datetime
import os

def read_json(filename="resources.json"):
    dir = os.path.dirname(os.path.abspath(__file__))
    resource_path = os.path.join(dir, filename)
    try:
        with open(resource_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return None

def write_json(data, filename="resources.json"):
    dir = os.path.dirname(os.path.abspath(__file__))
    resource_path = os.path.join(dir, filename)
    with open(resource_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

class FileProcessing:
    def __init__(self, club):
        self.club = club
    
    def save_file(self, filename="CM_chess_club.json"):
        data = {"events": [event.to_dict() for event in self.club.events]}
        dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        
    def load_file(self, filename="CM_chess_club.json"):
        from main import Event
        dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(dir, filename)
        if not os.path.exists(path):
            return
        data = read_json(filename)
        if not data:
            return
        self.club.events = []
        for event_data in data.get("events", []):
            event = Event(event_data["id"], event_data["name"], event_data["type"],
                         datetime.fromisoformat(event_data["start"]),
                         datetime.fromisoformat(event_data["end"]))
            for resource_id in event_data.get("resources", []):
                resource = self.club.search_resource(resource_id)
                if resource:
                    event.add_resource(resource)
            self.club.events.append(event)
