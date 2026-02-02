# Critical Mass Chess Club - Event Scheduler

Sistema para planificar eventos del club Critical Mass. Elegí este dominio por mi pasión por el ajedrez, considero que un club local de ajedrez tiene una versatilidad formidable en términos de manejo de actividades (como partidas amistosas, torneos, clases) en correlación con un inventario de recursos como tableros, piezas, relojes y personal facultado para su enseñanza y profesionales del juego.

El programa está escrito en inglés en su totalidad por comodidad del desarrollador.

## Funcionalidades

- Crear y listar eventos
- Validar que los recursos disponibles se usen correctamente
- Encontrar horarios libres
- Guardar/cargar datos en JSON
- Filtrar eventos por fecha

## Requisitos

En el programa predominan dos tipos de validacion:

**Correquisitos:** algunos recursos dependen de otro/s para que su selección sea permitida por el programa. Por ejemplo, una partida amistosa necesita tablero y piezas. El programa es estricto en cuanto a la ocurrencia de eventos restringidos.

**Exclusiones:** algunos recursos dependen del tipo de evento. Por ejemplo, los relojes solo pueden ser utilizados en torneos. El programa responde de la misma manera que en el caso de los correquisitos.

Todo está en `resources.json` y se valida automáticamente.


## Tipos de eventos

| ID | Nombre | Duración minima |
|----|--------|----------|
| `tournament` | Torneo | 2h |
| `class` | Clase | 1h |
| `team_match` | Enfrentamiento | 0.3h |
| `friendly_match` | Partida | 0.2h |
| `analysis` | Análisis | 0.5h |
| `simultaneous` | Simultánea | 1h |

---

## Instalacion y uso

### Opción 1: Instalación automática (recomendado)
```bash
cd /home/niitse/Documents/GitHub/cc
pip install -r requirements.txt
bash run.sh
```

### Opción 2: Instalación manual
```bash
pip install streamlit
bash run.sh
```

La web se ejecuta en la dirección: `http://localhost:8501`

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

## Notas

- Los eventos se guardan automáticamente en `CM_chess_club.json`.
- Los IDs son timestamps Unix.
- Valida duración, disponibilidad y restricciones en dicho orden.
- Busca huecos hora por hora en 7 días.
- Horario 24 horas, validación contra horarios de apertura y cierre.


# Desarrollado por Leonardo Córdova Rosas (C122)
## MATCOM, Universidad de La Habana.


