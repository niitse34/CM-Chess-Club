# Critical Mass Chess Club - Event Scheduler

Sistema para planificar eventos del club Critical Mass. Elegí este dominio por mi pasión por el ajedrez, considero que un club local de ajedrez tiene una versatilidad formidable en términos de manejo de eventos y recursos. El sistema organiza los recursos del club en tres categorías que reflejan de manera realista el modo de operacion de un club de ajedrez. El equipamiento incluye elementos físicos como tableros, piezas, relojes y piezas de repuesto, cada uno con disponibilidad limitada y sujeto a restricciones de uso simultáneo. Las salas representan los espacios físicos donde ocurren los eventos, es decir, el sistema las trata como recursos reservables que no pueden albergar dos actividades al mismo tiempo, forzando al usuario a considerar la capacidad de espacio del club al planificar. El personal agrupa a los entrenadores clasificados por su titulo FIDE (FIDE Master, International Master y Grandmaster), cuyo modelado incluye no solo su identidad sino también el seguimiento de su carga horaria semanal. Esta categorización no es solamente descriptiva, ya que el sistema utiliza la categoría de cada recurso para aplicar reglas de validación específicas. Por ejemplo, la exclusión de relojes en clases solo se aplica porque el sistema reconoce "reloj" como recurso de categoría equipamiento y "class" como tipo de evento incompatible según las reglas declaradas. La flexibilidad de poder añadir nuevas categorías desde el panel Settings (si el club adquiriera, por ejemplo, equipamiento informático para análisis asistido por computadora) da indicios de que el modelo de datos no está limitado por las categorías iniciales, sino que puede expandirse para reflejar la evolución real del club sin modificar el código original. Esta separación entre el modelo genérico de recursos y las reglas concretas de validación constituye una decisión de arquitectura que diferencia al sistema de un planificador de eventos convencional.

El programa está escrito en inglés en su totalidad por cuestiones de comodidad y fluidez.

## Decisiones de diseño

Se eligió Streamlit por su capacidad de generar interfaces funcionales sin separar frontend y backend, eliminando la gestión manual de estados. La persistencia automática en JSON evita pérdida de datos entre recargas. Los timestamps Unix como IDs garantizan ordenamiento cronológico y unicidad sin dependencias externas. Se prefirió JSON por su legibilidad directa y portabilidad; la separación en resources.json (configuración) y CM_chess_club.json (eventos) respeta el principio de responsabilidad única. Las reglas de negocio (correquisitos, exclusiones, días bloqueados, pool de piezas) residen en archivos de configuración editables desde la interfaz, cumpliendo el principio abierto/cerrado. Las validaciones se ejecutan en cascada (duración -> disponibilidad-> restricciones) para minimizar complejidad. La alerta de entrenador ocupado es permisiva, pues sugiere alternativas sin cancelar la decisión del usuario.

## Funcionalidades

- Crear y listar eventos
- Validar que los recursos disponibles se usen correctamente
- Encontrar horarios libres
- Guardar/cargar datos en JSON
- Filtrar eventos por fecha

Gestión de eventos.

 El sistema permite crear eventos de seis tipos (torneo, clase, enfrentamiento, partida amistosa, análisis y simultánea) especificando fecha, hora de inicio y recursos necesarios. Cada tipo de evento tiene una duración mínima configurable que el sistema exige cumplir antes de aceptar la creación. Los eventos existentes se despliegan en una tabla interactiva con ordenamiento cronológico descendente, permitiendo al usuario inspeccionar rápidamente la agenda del club. El filtrado por fecha acota la vista a días concretos sin necesidad de navegar manualmente entre grandes cantidades de registros, una funcionalidad que es apreciada cuando el club acumula semanas de actividad.

Validación automática de recursos.

 Al intentar agendar un evento, el sistema cruza los recursos seleccionados contra las reglas definidas en resources.json. Existen dos tipos de validación que operan de forma estricta. Los correquisitos exigen que ciertos recursos se reserven simultáneamente; el ejemplo base es la partida amistosa, que requiere tablero y piezas como conjunto inseparable. Si el usuario selecciona uno pero omite el otro, el sistema rechaza la operación indicando exactamente qué recurso falta. Las exclusiones, por su parte, impiden combinar recursos con tipos de evento incompatibles, o sea, los relojes de ajedrez solo pueden asociarse a torneos, y cualquier intento de usarlos en una clase o un análisis será bloqueado con un mensaje descriptivo. Estas reglas no están explicitas en el código fuente sino declaradas en el archivo de configuración, lo que permite modificarlas sin tocar la lógica del programa.

Búsqueda inteligente de horarios libres.

 La función "find_next_slot" constituye uno de los componentes más útiles del sistema. Dado un conjunto de recursos requeridos y una duración deseada, explora hora por hora los próximos siete días en busca del primer intervalo donde todos los recursos estén disponibles simultáneamente. La búsqueda respeta el horario de apertura y cierre del club definido en la configuración, omite automáticamente los días bloqueados que el usuario haya establecido, y descarta cualquier franja horaria donde exista solapamiento con eventos ya registrados. El resultado se presenta al usuario como una sugerencia que puede aceptar o ignorar, agilizando mucho el proceso de planificación frente a la alternativa de probar manualmente distintas combinaciones de fecha y hora.

Persistencia y configuración dinámica.

 Los eventos creados se guardan automáticamente en CM_chess_club.json inmediatamente después de cada operación de alta o eliminación, eliminando el riesgo de pérdida de datos por interrupciones. Desde el panel "settings", accesible en la barra lateral de la interfaz, el usuario tiene control total sobre la configuración del sistema. Puede crear nuevos tipos de evento definiendo su ID, nombre descriptivo y duración mínima requerida. Puede incorporar recursos adicionales al inventario del club especificando categoría, identificador, nombre y tipo. Puede establecer nuevas restricciones de correquisito o exclusión entre recursos y tipos de evento, o eliminar cualquier regla existente en desuso. Todos estos cambios modifican resources.json y surten efecto inmediato sobre las validaciones del sistema sin necesidad de reiniciar la aplicación. Como medida preventiva, un botón de restauración revierte la configuración completa a los valores por defecto, permitiendo al usuario experimentar sin temor a consecuencias permanentes.

Monitoreo de carga de entrenadores.

 Al seleccionar un entrenador (categorizado como FIDE Master, International Master o Grandmaster) el sistema calcula en tiempo real las horas acumuladas por ese profesional en los próximos siete días. Si la suma supera las cuarenta y ocho horas semanales, se despliega una alerta visual que muestra la carga actual junto con una sugerencia automática del entrenador con menos horas asignadas como alternativa. Esta funcionalidad sigue un modelo permisivo: el sistema recomienda pero no impide, partiendo de la premisa de que el usuario puede poseer información contextual que justifique la sobrecarga (por ejemplo, el consentimiento explícito del entrenador o la naturaleza extraordinaria de un evento que requiere su presencia a pesar del exceso horario).

Gestión de piezas de repuesto.

 El club dispone de un inventario limitado de piezas de repuesto para cubrir imprevistos durante los eventos. El sistema modela este recurso mediante dos parámetros configurables: el pool total disponible por día y la cantidad reservada por evento. Al agendar un nuevo evento, el sistema suma todas las piezas ya comprometidas por otros eventos en la misma fecha y añade las requeridas por el nuevo, es decir, si el total excede el límite diario, la creación se rechaza informando cuántas piezas faltarían. El usuario puede especificar una cantidad personalizada de piezas por evento o dejar el valor en cero para usar el valor por defecto, proporcionando flexibilidad para eventos que requieran mayor o menor previsión de material.



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

```bash
pip install -r requirements.txt
bash run.sh
```

La web se ejecuta en la dirección: `http://localhost:8501`

## Estructura

```
chess_club/
├── main.py           # programa
├── models.py       # clases y funciones auxiliares
├── resources.json    # configuración, archivo para persistencia de datos
├── CM_chess_club.json # eventos guardados durante la ejecucion de la aplicacion
├── run.sh           # ejecutar
└── report.md        # archivo actual
```


## Configuración del usuario

Desde el panel **Settings** en la interfaz, el usuario puede:

- **Crear tipos de evento** con ID, nombre y duración mínima.
- **Agregar recursos** (equipamiento, salas o personal) indicando categoría, ID, nombre y tipo.
- **Definir restricciones**: correquisitos o exclusiones.
- **Eliminar** cualquier tipo de evento, recurso o restricción existente.
- **Restaurar valores por defecto** con un solo botón, revirtiendo `resources.json` al estado original.

Todos los cambios persisten en `resources.json`.


Debugging realizado

Se realizaron pruebas sistemáticas durante el desarrollo del proyecto, cubriendo cada tipo de evento y recurso. Casos representativos incluyen: torneo sin relojes asignados (rechazado por correquisito), entrenador con más de 48 horas semanales (alerta visual con sugerencia de alternativa), evento en día bloqueado (rechazado con indicación del próximo día hábil), clase de 30 minutos (rechazada por duración inferior a la mínima), y reserva de piezas que excede el pool diario (rechazada con desglose del consumo). Se verificó la persistencia de datos cerrando y reabriendo la aplicación. El botón de restaurar valores por defecto fue probado tras varias modificaciones acumuladas. 

Lecciones asimiladas durante el desarrollo

El proyecto evidenció la importancia de externalizar las reglas del dominio desde el inicio. En un primer modelado y lanzamiento, los correquisitos y exclusiones estaban integrados en condicionales dentro del código, luego, al añadir el tercer tipo de restricción, el archivo principal se volvió difícil de mantener. Migrar esas reglas a resources.json simplificó drásticamente las ampliaciones posteriores. Otra lección relevante fue la gestión del estado en Streamlit. Al reconstruirse la interfaz completa en cada interacción, fue necesario diseñar cuidadosamente qué datos residen en los archivos JSON, cuáles en el session state del framework y cuáles se recalculan en cada ciclo. Finalmente, modelar el pool de piezas como un recurso diario en lugar de un inventario absoluto respondió a la realidad del club: las piezas se gastan, se reponen y su disponibilidad se razona por jornada, no como stock permanente, lo cual constituye a su vez un esfuerzo por implementar funcionalidades interesantes y atractivas en el programa.

## Notas

- Los eventos se guardan automáticamente en `CM_chess_club.json`.
- Valida duración, disponibilidad y restricciones en dicho orden.
- Busca huecos hora por hora en 7 días.
- Horario 24 horas, validación contra horarios de apertura y cierre.
- Validacion contra dias no laborables (blocked days).
- Pool de piezas de repuesto: el club dispone de un número limitado de piezas de repuesto por día (`spare_per_day`, por defecto 50). Cada evento reserva una cantidad de piezas (`spare_per_event`, por defecto 10). Al agendar un evento, el sistema suma las piezas ya reservadas por otros eventos del mismo día más las del nuevo evento y, si el total excede el pool diario, el evento es rechazado. El usuario puede especificar una cantidad personalizada de piezas por evento desde la interfaz (o dejar 0 para usar el valor por defecto). Ambos valores son configurables desde `resources.json` (`config.spare_per_day`, `config.spare_per_event`) y desde la interfaz en la sección save/load.


# Desarrollado por Leonardo Córdova Rosas (C122)
## MATCOM, Universidad de La Habana.


