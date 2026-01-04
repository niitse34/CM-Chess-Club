
import streamlit as st
import json
from datetime import datetime, timedelta, date
import os
from functions import read_json, write_json


st.set_page_config(
    page_title="Club de Ajedrez - Planificador",
    layout="wide"
)

# Título principal
st.title("Club de Ajedrez - Planificador de Eventos")
st.markdown("---")

# Clases para el sistema
class Recurso:
    def __init__(self, id, nombre, tipo, disponible=True):
        self.id = id
        self.nombre = nombre
        self.tipo = tipo
        self.disponible = disponible
        self.eventos_asignados = []

class Evento:
    def __init__(self, id, nombre, tipo, inicio, fin):
        self.id = id
        self.nombre = nombre
        self.tipo = tipo
        self.inicio = inicio
        self.fin = fin
        self.recursos = []
        self.estado = "planificado"
    
    def agregar_recurso(self, recurso):
        self.recursos.append(recurso)
    
    def se_solapa_con(self, otro_evento):
        return (self.inicio < otro_evento.fin and self.fin > otro_evento.inicio)
    
    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "inicio": self.inicio.isoformat(),
            "fin": self.fin.isoformat(),
            "recursos": [r.id for r in self.recursos],
            "estado": self.estado
        }

class ClubAjedrez:
    def buscar_recurso(self, recurso_id):
        for recurso in self.recursos:
            if recurso.id == recurso_id:
                return recurso

    def verificar_disponibilidad(self, recurso_id, inicio, fin):
        recurso = self.buscar_recurso(recurso_id)
        if not recurso:
            return False
        for evento in self.eventos:
            if recurso in evento.recursos:
                if not (fin <= evento.inicio or inicio >= evento.fin):
                    return False
        return True

    def obtener_inicio_evento(self, evento):
        return evento.inicio

    def __init__(self):
        self.recursos = []
        self.eventos = []
        self.restricciones = []
        self.cargar_datos_iniciales()
    
    def cargar_datos_iniciales(self):
        # Cargar datos desde resources.json (ruta absoluta)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        resource_path = os.path.join(base_dir, "resources.json")
        try:
            with open(resource_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            st.error(f"Archivo resources.json no encontrado en {resource_path}")
            return
        
        # Cargar recursos
        self.recursos = []
        # Espacios
        for espacio in data.get("espacios", []):
            self.recursos.append(Recurso(
                id=espacio["id"],
                nombre=espacio["nombre"],
                tipo="espacio",
                disponible=True
            ))
        # Equipamiento
        for equipo in data.get("equipamiento", []):
            self.recursos.append(Recurso(
                id=equipo["id"],
                nombre=equipo["nombre"],
                tipo="equipamiento",
                disponible=True
            ))
        # Personal
        for persona in data.get("personal", []):
            self.recursos.append(Recurso(
                id=persona["id"],
                nombre=persona["nombre"],
                tipo="personal",
                disponible=True
            ))
        # Cargar restricciones desde JSON
        self.restricciones = data.get("restricciones", [])
        # Cargar tipos de evento para referencia
        self.tipos_evento = {tipo["id"]: tipo for tipo in data.get("tipos_evento", [])}
        # Cargar configuración
        self.config = data.get("config", {})

    def validar_restricciones(self, evento):
        # Verificar co-requisitos
        for restriccion in self.restricciones:
            if restriccion["tipo"] == "co_requisito":
                # Verificar si la restricción aplica a este tipo de evento
                if restriccion.get("caso") == evento.tipo:
                    recursos_evento_ids = [r.id for r in evento.recursos]
                    requiere = restriccion.get("requiere", [])
                    cantidad_minima = restriccion.get("cantidad_minima", 1)
                    # Para partida amistosa, debe haber al menos un tablero y unas piezas
                    if evento.tipo == "partida":
                        tiene_tablero = any(rid.startswith("tablero_") for rid in recursos_evento_ids)
                        tiene_piezas = any(rid.startswith("piezas_") for rid in recursos_evento_ids)
                        if not (tiene_tablero and tiene_piezas):
                            return False, "Falta tablero y/o piezas para partida amistosa"
                    else:
                        # Contar cuántos recursos requeridos están presentes
                        count = sum(1 for req in requiere if req in recursos_evento_ids)
                        if count < cantidad_minima:
                            return False, f"Falta recurso requerido para {evento.tipo}: necesita al menos {cantidad_minima} de {requiere}"
        
        # Verificar exclusiones
        for restriccion in self.restricciones:
            if restriccion["tipo"] == "exclusion":
                recursos_afectados = restriccion.get("recursos", [])
                eventos_permitidos = restriccion.get("eventos_permitidos", [])
                
                # Si el evento usa recursos afectados y no está en eventos permitidos
                if any(r.id in recursos_afectados for r in evento.recursos):
                    if evento.tipo not in eventos_permitidos:
                        return False, f"Recurso restringido: {restriccion.get('nombre', 'Restricción de exclusión')}"
        
        return True, "OK"
    
    def planificar_evento(self, nombre, tipo, inicio, fin, recursos_ids):
        # Verificar duración válida
        if fin <= inicio:
            return False, "La hora de fin debe ser posterior a la de inicio"
        
        # Calcular duración en horas
        duracion_horas = (fin - inicio).total_seconds() / 3600
        
        # Validar duración mínima y máxima desde config
        duracion_min = self.config.get("duracion_minima", 0.5)
        duracion_max = self.config.get("duracion_maxima", 8.0)
        if duracion_horas < duracion_min or duracion_horas > duracion_max:
            return False, f"Duración debe estar entre {duracion_min} y {duracion_max} horas"
        
        # Validar duración contra el tipo de evento si existe
        if tipo in self.tipos_evento:
            duracion_esperada = self.tipos_evento[tipo].get("duracion_horas", 0)
            if duracion_esperada > 0 and duracion_horas < duracion_esperada:
                return False, f"El tipo {tipo} requiere al menos {duracion_esperada} horas"
        
        # Crear evento temporal para validaciones
        evento_temp = Evento("temp", nombre, tipo, inicio, fin)
        
        # Verificar disponibilidad de recursos
        recursos_asignados = []
        for recurso_id in recursos_ids:
            if not self.verificar_disponibilidad(recurso_id, inicio, fin):
                recurso = self.buscar_recurso(recurso_id)
                return False, f"Recurso {recurso.nombre if recurso else recurso_id} no disponible"
            recurso = self.buscar_recurso(recurso_id)
            if recurso:
                recursos_asignados.append(recurso)
                evento_temp.agregar_recurso(recurso)
        
        # Validar restricciones
        valido, mensaje = self.validar_restricciones(evento_temp)
        if not valido:
            return False, mensaje
        
        # Crear evento definitivo
        evento_id = f"evento_{len(self.eventos) + 1:03d}"
        evento = Evento(evento_id, nombre, tipo, inicio, fin)
        for recurso in recursos_asignados:
            evento.agregar_recurso(recurso)
        
        self.eventos.append(evento)
        return True, f"Evento '{nombre}' planificado exitosamente"
    
    def buscar_proximo_hueco(self, duracion_horas, recursos_ids):
        ahora = datetime.now()
        
        # Comenzar desde la próxima hora en punto
        hora_actual = ahora.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
        # Buscar durante los próximos 7 días
        for _ in range(24 * 7):  # Cada hora por 7 días
            fin_propuesto = hora_actual + timedelta(hours=duracion_horas)
            
            # Verificar disponibilidad para todos los recursos
            todos_disponibles = all(
                self.verificar_disponibilidad(rid, hora_actual, fin_propuesto)
                for rid in recursos_ids
            )
            
            if todos_disponibles:
                return hora_actual
            
            hora_actual += timedelta(hours=1)
        
        return None
    
    def eliminar_evento(self, evento_id):
        for i, evento in enumerate(self.eventos):
            if evento.id == evento_id:
                del self.eventos[i]
                return True
        return False
    
    def guardar_a_archivo(self, filename="club_ajedrez.json"):
        data = {
            "eventos": [evento.to_dict() for evento in self.eventos],
            "recursos": [
                {
                    "id": r.id,
                    "nombre": r.nombre,
                    "tipo": r.tipo,
                    "disponible": r.disponible
                }
                for r in self.recursos
            ]
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def cargar_desde_archivo(self, filename="club_ajedrez.json"):
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Cargar eventos
            self.eventos = []
            for evento_data in data.get("eventos", []):
                evento = Evento(
                    evento_data["id"],
                    evento_data["nombre"],
                    evento_data["tipo"],
                    datetime.fromisoformat(evento_data["inicio"]),
                    datetime.fromisoformat(evento_data["fin"])
                )
                evento.estado = evento_data.get("estado", "planificado")
                
                # Asignar recursos
                for recurso_id in evento_data.get("recursos", []):
                    recurso = self.buscar_recurso(recurso_id)
                    if recurso:
                        evento.agregar_recurso(recurso)
                
                self.eventos.append(evento)

# Inicializar el club
if 'club' not in st.session_state:
    st.session_state.club = ClubAjedrez()
    st.session_state.club.cargar_desde_archivo()

club = st.session_state.club

# Sidebar para navegación
with st.sidebar:
    st.header("Navegación")
    opcion = st.radio(
        "Selecciona una opción:",
        ["Ver Eventos", "Planificar Evento", "Buscar Hueco", 
         "Eliminar Evento", "Guardar/Cargar", "Recursos"]
    )
    
    st.markdown("---")
    st.header("Información del Club")
    st.info(f"Recursos disponibles: {len(club.recursos)}")
    st.info(f"Eventos planificados: {len(club.eventos)}")
    
    # Mostrar próximos eventos
    if club.eventos:
        st.subheader("Próximos eventos:")
        hoy = datetime.now()
        proximos = sorted(
            [e for e in club.eventos if e.inicio > hoy],
            key=lambda e: e.inicio
        )[:3]
        
        for evento in proximos:
            st.write(f"{evento.nombre}")
            st.caption(f"  {evento.inicio.strftime('%d/%m %H:%M')}")

# Contenido principal según opción seleccionada
if opcion == "Ver Eventos":
    st.header("Eventos Planificados")
    
    if not club.eventos:
        st.warning("No hay eventos planificados.")
    else:
        # Filtrar por fecha
        col1, col2 = st.columns(2)
        with col1:
            filtrar_fecha = st.checkbox("Filtrar por fecha")
        
        eventos_filtrados = club.eventos
        
        if filtrar_fecha:
            with col2:
                fecha_filtro = st.date_input("Seleccionar fecha", date.today())
                eventos_filtrados = [
                    e for e in club.eventos 
                    if e.inicio.date() == fecha_filtro
                ]
        
        # Mostrar eventos
        for evento in sorted(eventos_filtrados, key=lambda e: e.inicio):
            with st.expander(f"**{evento.nombre}** ({evento.tipo})"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Inicio:** {evento.inicio.strftime('%d/%m/%Y %H:%M')}")
                with col2:
                    st.write(f"**Fin:** {evento.fin.strftime('%H:%M')}")
                with col3:
                    st.write(f"**Duración:** {(evento.fin - evento.inicio).seconds // 3600}h")
                
                st.write("**Recursos asignados:**")
                recursos_cols = st.columns(3)
                for i, recurso in enumerate(evento.recursos):
                    with recursos_cols[i % 3]:
                        st.info(f"• {recurso.nombre}")

elif opcion == "Planificar Evento":
    st.header("Planificar Nuevo Evento")
    
    with st.form("planificar_evento"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre del evento", placeholder="Ej: Torneo Clasificatorio")
            tipo = st.selectbox("Tipo de evento", options=list(club.tipos_evento.keys()), format_func=lambda x: club.tipos_evento[x]["nombre"])
        with col2:
            fecha = st.date_input("Fecha", date.today())
            hora_inicio = st.time_input("Hora de inicio", value=datetime.now().time())
            min_dur = float(club.config.get("duracion_minima", 0.5))
            max_dur = float(club.config.get("duracion_maxima", 8.0))
            duracion = st.number_input("Duración (horas)", min_value=min_dur, max_value=max_dur, step=0.5, value=2.0)
        inicio = datetime.combine(fecha, hora_inicio)
        fin = inicio + timedelta(hours=duracion)
        st.subheader("Seleccionar Recursos")
        recursos_por_tipo = {}
        for recurso in club.recursos:
            if recurso.tipo not in recursos_por_tipo:
                recursos_por_tipo[recurso.tipo] = []
            recursos_por_tipo[recurso.tipo].append(recurso)
        recursos_seleccionados = []
        for tipo_recurso, recursos in recursos_por_tipo.items():
            st.write(f"**{tipo_recurso.capitalize()}:**")
            cols = st.columns(3)
            for i, recurso in enumerate(recursos):
                with cols[i % 3]:
                    if st.checkbox(recurso.nombre, key=f"recurso_{recurso.id}"):
                        recursos_seleccionados.append(recurso.id)
        # Botón para planificar (debe estar dentro del bloque form)
        submitted = st.form_submit_button("Planificar Evento")
        if submitted:
            if not nombre:
                st.error("Debe ingresar un nombre para el evento")
                st.rerun()
            elif not recursos_seleccionados:
                st.error("Debe seleccionar al menos un recurso")
                st.rerun()
            else:
                with st.spinner("Validando y planificando evento..."):
                    exitoso, mensaje = club.planificar_evento(nombre, tipo, inicio, fin, recursos_seleccionados)
                    if exitoso:
                        st.success(mensaje)
                        st.session_state.hueco_encontrado = None
                        st.rerun()
                    else:
                        st.error(f"Error: {mensaje}")
                        st.rerun()


elif opcion == "Buscar Hueco":
    st.header("Buscar Hueco Disponible")

    # Espacio para eventos especiales (implementación futura)
    # ------------------------------------------------------
    # Aquí puedes agregar lógica para eventos especiales, por ejemplo:
    # if st.button("Evento Especial: Puzzle Rush"):
    #     ...
    # ------------------------------------------------------

    with st.form("buscar_hueco"):
        min_dur = float(club.config.get("duracion_minima", 0.5))
        max_dur = float(club.config.get("duracion_maxima", 8.0))
        duracion = st.number_input(
            "Duración del evento (horas)",
            min_value=min_dur,
            max_value=max_dur,
            step=0.5, value=1.5)

        st.subheader("Seleccionar Recursos Necesarios")
        recursos_necesarios = []

        # Mostrar todos los recursos con checkboxes
        cols = st.columns(3)
        for i, recurso in enumerate(club.recursos):
            with cols[i % 3]:
                if st.checkbox(recurso.nombre, key=f"buscar_{recurso.id}"):
                    recursos_necesarios.append(recurso.id)

        buscar = st.form_submit_button("Buscar Próximo Hueco")

        if buscar:
            if not recursos_necesarios:
                st.error("Seleccione al menos un recurso")
            else:
                with st.spinner("Buscando hueco disponible..."):
                    hueco = club.buscar_proximo_hueco(duracion, recursos_necesarios)
                    if hueco:
                        fin_hueco = hueco + timedelta(hours=duracion)
                        st.success(f"s Hueco encontrado!")
                        st.info(f"**Disponible desde:** {hueco.strftime('%d/%m/%Y %H:%M')}")
                        st.info(f"**Hasta:** {fin_hueco.strftime('%H:%M')}")
                        # Opción para planificar directamente (usar otro submit fuera del form)
                        st.session_state.hueco_encontrado = {
                            "inicio": hueco,
                            "fin": fin_hueco,
                            "recursos": recursos_necesarios
                        }
                    else:
                        st.warning("No se encontró hueco disponible en los próximos 7 días")
    # Botón para planificar en el hueco encontrado (fuera del form)
    if st.session_state.get("hueco_encontrado"):
        st.markdown("---")
        st.subheader("Planificar evento en hueco encontrado")
        datos = st.session_state.hueco_encontrado
        with st.form("planificar_en_hueco"):
            nombre = st.text_input("Nombre del evento", placeholder="Ej: Torneo Rápido")
            tipo = st.selectbox("Tipo de evento", options=list(club.tipos_evento.keys()), format_func=lambda x: club.tipos_evento[x]["nombre"])
            recursos = datos["recursos"]
            st.write(f"Recursos seleccionados: {', '.join(recursos)}")
            submitted = st.form_submit_button("Planificar en este hueco")
            if submitted:
                if not nombre:
                    st.error("Debe ingresar un nombre para el evento")
                else:
                    exitoso, mensaje = club.planificar_evento(
                        nombre, tipo, datos["inicio"], datos["fin"], recursos
                    )
                    if exitoso:
                        st.success(mensaje)
                        st.session_state.hueco_encontrado = None
                        st.rerun()
                    else:
                        st.error(f"Error: {mensaje}")

elif opcion == "Eliminar Evento":
    st.header("Eliminar Evento")
    
    if not club.eventos:
        st.warning("No hay eventos para eliminar.")
    else:
        # Listar eventos con opción para eliminar
        evento_seleccionado = st.selectbox(
            "Seleccionar evento a eliminar:",
            options=[f"{e.id}: {e.nombre} ({e.inicio.strftime('%d/%m %H:%M')})" 
                    for e in club.eventos]
        )
        
        if evento_seleccionado:
            evento_id = evento_seleccionado.split(":")[0]
            
            # Mostrar detalles del evento seleccionado
            evento = next((e for e in club.eventos if e.id == evento_id), None)
            if evento:
                st.write(f"**Nombre:** {evento.nombre}")
                st.write(f"**Tipo:** {evento.tipo}")
                st.write(f"**Fecha y hora:** {evento.inicio.strftime('%d/%m/%Y %H:%M')}")
                st.write(f"**Recursos asignados:** {len(evento.recursos)} recursos")
                
                # Confirmar eliminación
                if st.button("Confirmar Eliminación", type="secondary"):
                    if club.eliminar_evento(evento_id):
                        st.success(" Evento eliminado exitosamente")
                        st.rerun()
                    else:
                        st.error("Error al eliminar el evento")

elif opcion == "Guardar/Cargar":
    st.header("Guardar y Cargar Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Guardar Datos")
        if st.button("Guardar todo en archivo"):
            club.guardar_a_archivo()
            st.success("Datos guardados en club_ajedrez.json")
    
    with col2:
        st.subheader("Cargar Datos")
        archivo = st.file_uploader("Seleccionar archivo JSON", type=['json'])
        if archivo is not None:
            if st.button("Cargar datos"):
                # Guardar archivo temporalmente
                with open("temp_load.json", "wb") as f:
                    f.write(archivo.getvalue())
                
                club.cargar_desde_archivo("temp_load.json")
                st.success("Datos cargados exitosamente")
                st.rerun()
    
    # Mostrar vista previa de datos
    st.subheader("Vista Previa de Datos")
    if st.checkbox("Mostrar datos en JSON"):
        data = {
            "eventos": [evento.to_dict() for evento in club.eventos[:3]],  # Mostrar solo 3
            "total_eventos": len(club.eventos),
            "recursos": len(club.recursos)
        }
        st.json(data)

elif opcion == "Recursos":
    st.header("Recursos del Club")
    
    # Mostrar recursos por tipo
    tipos = set([r.tipo for r in club.recursos])
    
    for tipo in tipos:
        st.subheader(f"{tipo.capitalize()}s")
        recursos_tipo = [r for r in club.recursos if r.tipo == tipo]
        
        cols = st.columns(3)
        for i, recurso in enumerate(recursos_tipo):
            with cols[i % 3]:
                # Calcular disponibilidad
                eventos_con_recurso = [
                    e for e in club.eventos 
                    if recurso.id in [r.id for r in e.recursos]
                ]
                
                # Crear tarjeta de recurso
                with st.container():
                    st.write(f"{recurso.nombre}")
                    
                    if recurso.disponible:
                        st.success("Disponible")
                    else:
                        st.error("No disponible")
                    
                    if eventos_con_recurso:
                        st.caption(f"Usado en {len(eventos_con_recurso)} eventos")
                        # Mostrar próximos eventos con este recurso
                        proximos = sorted(
                            [e for e in eventos_con_recurso if e.inicio > datetime.now()],
                            key=lambda e: e.inicio
                        )[:2]
                        for evento in proximos:
                            st.caption(f"{evento.nombre}: {evento.inicio.strftime('%d/%m %H:%M')}")
        