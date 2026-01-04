import json
import datetime as dt


# leer json
def read_json(path="resources.json"):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

# escribir json
def write_json(data, path="resources.json"):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


