import streamlit as st
import json
import datetime as dt
from functions import read_json,write_json

#classes

class Recurso:
    def __init__(self,id,nombre,tipo,disponible = True):
        self.id = id
        self.nombre = nombre
        self.tipo = tipo
        self.disponible = disponible
        self.en_uso_por = []
        
        
class Evento:
    def __init__(self,id,nombre,fecha,hora_inicio,hora_fin,recursos_asignados=[]):
        self.id = id
        self.nombre = nombre
        self.fecha = fecha
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.recursos_asignados = recursos_asignados
        
    

  



