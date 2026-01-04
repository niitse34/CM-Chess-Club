import json
import datetime as dt


# Leer desde un archivo JSON (ruta configurable)
def read_json(path="resources.json"):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

# Escribir en un archivo JSON (ruta configurable)
def write_json(data, path="resources.json"):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

# Espacio para funciones de eventos especiales (implementación futura)
# def evento_especial_puzzle_rush(...):
#     pass

