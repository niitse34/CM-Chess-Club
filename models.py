from datetime import datetime

class Resource:
    def __init__(self,id,name,type):
        self.id = id
        self.name = name
        self.type = type
        
class Event:
    def __init__(self,id,name,type,start,end,spare_pieces=None):
        self.id = id
        self.name = name
        self.type = type
        self.start = start
        self.end = end
        self.resources = []
        self.spare_pieces = spare_pieces  #none means use default per event policy
        
    def add_resource(self,resource):
        self.resources.append(resource)
        
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "resources": [i.id for i in self.resources],
            "spare_pieces": self.spare_pieces
        }
