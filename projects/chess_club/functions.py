import json
import datetime as dt

#read from json
def read_json():
    with open("resources.json", "r") as file:
        return json.load(file)
#write into json
def write_json(data):
    with open("resources.json", "w") as file:
        json.dump(data, file)
        
