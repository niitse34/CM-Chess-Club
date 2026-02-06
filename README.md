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

### Condiciones óptimas

**Busy Coach (Entrenador ocupado):** el sistema monitorea la carga de trabajo de cada entrenador (FM, IM, GM) en los próximos 7 días. Al crear un evento, si el entrenador seleccionado acumula más de 48 horas de eventos en la semana, se muestra una alerta visual en la interfaz con su carga actual. El sistema tambien sugiere automáticamente al entrenador con menos horas asignadas como alternativa. Esta funcionalidad es permisiva: el usuario puede ignorar la sugerencia y agendar al entrenador ocupado de todas formas.

**Días bloqueados:** el sistema permite definir días de la semana en los que no se permiten eventos. Se configuran en `resources.json` bajo `config.blocked_days` (ej: `["Monday"]`). Los días deben escribirse con su nombre completo en inglés. El buscador de horarios (`find_next_slot`) también respeta esta restricción y omite los días bloqueados.


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

### Opción 1: Instalación automática
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


## Configuración del usuario

Desde el panel **Settings** en la interfaz, el usuario puede:

- **Crear tipos de evento** con ID, nombre y duración mínima.
- **Agregar recursos** (equipamiento, salas o personal) indicando categoría, ID, nombre y tipo.
- **Definir restricciones**: correquisitos o exclusiones.
- **Eliminar** cualquier tipo de evento, recurso o restricción existente.
- **Restaurar valores por defecto** con un solo botón, revirtiendo `resources.json` al estado original.

Todos los cambios persisten en `resources.json`.

## Notas

- Los eventos se guardan automáticamente en `CM_chess_club.json`.
- Los IDs son timestamps Unix.
- Valida duración, disponibilidad y restricciones en dicho orden.
- Busca huecos hora por hora en 7 días.
- Horario 24 horas, validación contra horarios de apertura y cierre.
- Validacion contra dias no laborables (blocked days).
- *Pool de piezas de repuesto:* el club dispone de un número limitado de piezas de repuesto por día (`spare_per_day`, por defecto 50). Cada evento reserva una cantidad de piezas (`spare_per_event`, por defecto 10). Al agendar un evento, el sistema suma las piezas ya reservadas por otros eventos del mismo día más las del nuevo evento; si el total excede el pool diario, el evento es rechazado. El usuario puede especificar una cantidad personalizada de piezas por evento desde la interfaz (o dejar 0 para usar el valor por defecto). Ambos valores son configurables desde `resources.json` (`config.spare_per_day`, `config.spare_per_event`) y desde la interfaz en la sección save/load.


# Desarrollado por Leonardo Córdova Rosas (C122)
## MATCOM, Universidad de La Habana.


