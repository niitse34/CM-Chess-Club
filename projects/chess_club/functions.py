import json
import datetime as dt
import os
from datetime import datetime, timedelta


#read json
def read_json(path=None):
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "resources.json")
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

#write json
def write_json(data, path=None):
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "resources.json")
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)