# Critical Mass Chess Club - Event Scheduler

Sistema para planificar eventos del club Critical Mass. Elegi este dominio por mi pasion por el ajedrez y porque necesitaba algo para manejar recursos y horarios sin complicaciones.

El código está en inglés por preferencia personal.
## Qué hace

- Crear y listar eventos
- Validar que los recursos disponibles se usen correctamente
- Encontrar horarios libres
- Guardar/cargar todo en JSON
- Filtrar eventos por fecha

---

## Requisitos (cómo funcionan)

Hice dos tipos de validación:

**Co-requisitos:** algunos recursos deben ir juntos. Por ejemplo, una partida amistosa necesita tablero Y piezas. Si intentas programar sin ambos, impide la planificacion.

**Exclusiones:** algunos recursos solo se usan en ciertos eventos. Los relojes solo en torneos. Si intentas usar un reloj en una partida casual, impide la planificacion.

Todo está en `resources.json` y se valida automáticamente.

---

## Tipos de eventos

| ID | Nombre | Duración |
|----|--------|----------|
| `tournament` | Torneo | 2h |
| `class` | Clase | 1h |
| `team_match` | Enfrentamiento | 1.5h |
| `friendly_match` | Partida | 0.5h |
| `analysis` | Análisis | 1h |
| `simultaneous` | Simultánea | 1.5h |

---

## Instalar y usar

```bash
cd /home/niitse/Documents/GitHub/cc/projects/chess_club
pip install streamlit
bash run.sh
```

Abre `http://localhost:8501`

---

## Estructura

```
chess_club/
├── main.py           # la app
├── resources.json    # configuración
├── CM_chess_club.json # eventos (se genera)
├── run.sh           # ejecutar
└── README.md        # esto
```

---

## Agregar cosas nuevas

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

- Los eventos se guardan automáticamente en `CM_chess_club.json`
- Los IDs son timestamps Unix
- Valida duración, disponibilidad y restricciones en ese orden
- Busca huecos hora por hora en 7 días
- Horario 24h, validación contra opening/closing times



