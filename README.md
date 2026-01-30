# Critical Mass Chess Club - Event Scheduler

Sistema para planificar eventos del club Critical Mass. Elegi este dominio por mi pasion por el ajedrez, considero que un club local de ajedrez tiene una versatilidad formidable en terminos de manejo de actividades(como partidas amistosas, torneos, clases) en correlacion con un inventario de recursos como tableros, piezas, relojes y personal facultado para su ensennanza y profesionales del juego.

El programa esta escrito en ingles en su totalidad por comodidad del desarrollador.

## Funcionalidades

- Crear y listar eventos
- Validar que los recursos disponibles se usen correctamente
- Encontrar horarios libres
- Guardar/cargar datos en JSON
- Filtrar eventos por fecha

## Requisitos

En el programa predominan dos tipos de validacion:

**Correquisitos:** algunos recursos dependen de otro/s para que su seleccion sea permitida por el programa. Por ejemplo, una partida amistosa necesita tablero y piezas. El programa es estricto en cuanto a la ocurrencia de eventos restringidos.

**Exclusiones:** algunos recursos dependen del tipo de evento. Por ejemplo, los relojes solo pueden ser utilizados en torneos. El programa responde de la misma manera que en el caso de los correquisitos

Todo está en `resources.json` y se valida automáticamente.


## Tipos de eventos

| ID | Nombre | Duración predeterminada |
|----|--------|----------|
| `tournament` | Torneo | 2h |
| `class` | Clase | 1h |
| `team_match` | Enfrentamiento | 1.5h |
| `friendly_match` | Partida | 0.5h |
| `analysis` | Análisis | 1h |
| `simultaneous` | Simultánea | 1.5h |

---

## Instalacion y uso

```bash
cd /home/niitse/Documents/GitHub/cc/projects/chess_club
pip install streamlit
bash run.sh
```

la web se ejecuta en la direccion: `http://localhost:8501`

---

## Estructura

```
chess_club/
├── main.py           # programa
├── resources.json    # configuración, archivo para persistencia de datos
├── CM_chess_club.json # eventos guardados durante la ejecucion de la aplicacion
├── run.sh           # ejecutar
└── README.md        # archivo actual
```


## Agregar datos al json

**Nuevo tipo de evento:**
```json
{
  "id": "lightning",
  "name": "Lightning",
  "min_duration": 0.5
}
```

**Nuevo requisito:**
```json
{
  "type": "co_requirement",
  "name": "Lightning needs a clock",
  "case": "lightning",
  "requires": ["clock_1", "clock_2"],
  "min_amount": 1
}
```

**Nuevo recurso:**
```json
{
  "id": "board_5",
  "name": "Board 5",
  "type": "board"
}
```

**Nueva sección en GUI:**
Agrega en `main.py` bajo `#pages`:
```python
elif page == "Nueva Seccion":
    st.header("Nueva Seccion")
    # código aquí
```

---

## Notas

- Los eventos se guardan automáticamente en `CM_chess_club.json`.
- Los IDs son timestamps Unix.
- Valida duración, disponibilidad y restricciones en dicho orden.
- Busca huecos hora por hora en 7 días.
- Horario 24h, validación contra opening/closing times.

##              Desarrollado por Leonardo Cordova Rosas
# MATCOM, Universidad de La Habana.


