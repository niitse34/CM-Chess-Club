import streamlit as st
import json
from datetime import datetime, timedelta, date
import os


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
        @     b n 
        def obtener_inicio_evento(evento):
            return evento.inicio
    def __init__(self):
        self.recursos = []
        self.eventos = []
        self.restricciones = []
        self.cargar_datos_iniciales()
    
    def cargar_datos_iniciales(self):
        # Recursos básicos del club
        recursos_data = [
            {"id": "sala_principal", "nombre": "Sala Principal", "tipo": "espacio"},
            {"id": "tablero_01", "nombre": "Tablero de Torneo 1", "tipo": "equipamiento"},
            {"id": "tablero_02", "nombre": "Tablero de Torneo 2", "tipo": "equipamiento"},
            {"id": "tablero_03", "nombre": "Tablero Estándar 1", "tipo": "equipamiento"},
            {"id": "tablero_04", "nombre": "Tablero Estándar 2", "tipo": "equipamiento"},
            {"id": "reloj_01", "nombre": "Reloj Digital 1", "tipo": "equipamiento"},
            {"id": "reloj_02", "nombre": "Reloj Digital 2", "tipo": "equipamiento"},
            {"id": "instructor", "nombre": "Instructor Carlos", "tipo": "personal"},
            {"id": "arbitro", "nombre": "Árbitro María", "tipo": "personal"},
            {"id": "proyector", "nombre": "Proyector de Partidas", "tipo": "equipamiento"}
        ]
        
        for data in recursos_data:
            self.recursos.append(Recurso(**data))
        
        # Restricciones
        self.restricciones = [
            {
                "tipo": "co_requisito",
                "nombre": "Torneo requiere Árbitro",
                "descripcion": "Todo torneo debe tener un árbitro",
                "condicion": self.es_torneo,
                "recursos_requeridos": ["arbitro"]
            },
            {
                "tipo": "co_requisito",
                "nombre": "Clase requiere Instructor",
                "descripcion": "Toda clase debe tener un instructor",
                "condicion": self.es_clase,
                "recursos_requeridos": ["instructor"]
            },
            {
                "tipo": "exclusion",
                "nombre": "No torneo y clase simultáneos",
                "descripcion": "No puede haber torneo y clase al mismo tiempo",
                "condicion": self.torneo_y_clase_simultaneos
            }
        ]

    def es_torneo(self, evento):
        return evento.tipo == "torneo"

    def es_clase(self, evento):
        return evento.tipo == "clase"

    def torneo_y_clase_simultaneos(self, e1, e2):
        return (
            (e1.tipo == "torneo" and e2.tipo == "clase") or
            (e1.tipo == "clase" and e2.tipo == "torneo")
        )
    def validar_restricciones(self, evento):
        # Verificar co-requisitos
        for restriccion in self.restricciones:
            if restriccion["tipo"] == "co_requisito":
                if restriccion["condicion"](evento):
                    recursos_evento_ids = [r.id for r in evento.recursos]
                    for req in restriccion["recursos_requeridos"]:
                        if req not in recursos_evento_ids:
                            return False, f"Falta recurso requerido: {req}"
        
        # Verificar exclusiones
        for restriccion in self.restricciones:
            if restriccion["tipo"] == "exclusion":
                for otro_evento in self.eventos:
                    if evento.se_solapa_con(otro_evento):
                        if restriccion["condicion"](evento, otro_evento):
                            return False, f"Exclusión mutua con evento: {otro_evento.nombre}"
        
        return True, "OK"
    
    def planificar_evento(self, nombre, tipo, inicio, fin, recursos_ids):
        # Verificar duración válida
        if fin <= inicio:
            return False, "La hora de fin debe ser posterior a la de inicio"
        
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
            key=ClubAjedrez.obtener_inicio_evento
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
        for evento in sorted(eventos_filtrados, key=ClubAjedrez.obtener_inicio_evento):
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
            nombre = st.text_input("Nombre del evento", 
                                  placeholder="Ej: Torneo Clasificatorio")
            tipo = st.selectbox("Tipo de evento", 
                               ["torneo", "clase", "partida", "analisis", "simultaneas"])
        
        with col2:
            fecha = st.date_input("Fecha", date.today())
            hora_inicio = st.time_input("Hora de inicio", value=datetime.now().time())
            duracion = st.number_input("Duración (horas)", min_value=0.5, 
                                      max_value=8.0, step=0.5, value=2.0)
        
        inicio = datetime.combine(fecha, hora_inicio)
        fin = inicio + timedelta(hours=duracion)
        
        st.subheader("Seleccionar Recursos")
        
        # Mostrar recursos por categoría
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
        
        # Botón para planificar
        submitted = st.form_submit_button("Planificar Evento")
        
        if submitted:
            if not nombre:
                st.error("Debe ingresar un nombre para el evento")
            elif not recursos_seleccionados:
                st.error("Debe seleccionar al menos un recurso")
            else:
                with st.spinner("Validando y planificando evento..."):
                    exitoso, mensaje = club.planificar_evento(
                        nombre, tipo, inicio, fin, recursos_seleccionados
                    )
                    
                    if exitoso:
                        st.success(mensaje)
                        st.balloons()
                    else:
                        st.error(f"Error: {mensaje}")

elif opcion == "Buscar Hueco":
    st.header("Buscar Hueco Disponible")
    
    with st.form("buscar_hueco"):
        duracion = st.number_input("Duración del evento (horas)", 
                                  min_value=0.5, max_value=8.0, 
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
                        
                        # Opción para planificar directamente
                        if st.button("Planificar en este hueco"):
                            st.session_state.hueco_encontrado = {
                                "inicio": hueco,
                                "fin": fin_hueco,
                                "recursos": recursos_necesarios
                            }
                            st.experimental_rerun()
                    else:
                        st.warning("No se encontró hueco disponible en los próximos 7 días")

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
                        st.experimental_rerun()
                    else:
                        st.error("Error al eliminar el evento")

elif opcion == "Guardar/Cargar":
    st.header("Guardar y Cargar Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Guardar Datos")
        if st.button("Guardar todo en archivo"):
            club.guardar_a_archivo()
            st.success("Datos guardados en 'club_ajedrez.json'")
    
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
                st.experimental_rerun()
    
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
                            key=ClubAjedrez.obtener_inicio_evento
                        )[:2]
                        for evento in proximos:
                            st.caption(f"{evento.nombre}: {evento.inicio.strftime('%d/%m %H:%M')}")
        