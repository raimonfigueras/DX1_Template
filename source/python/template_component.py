# =============================================================================
# PLANTILLA DE COMPONENTE PARA SPEEDBEE SYNAPSE / DX1
# =============================================================================
#
# PROPÓSITO:
#   Este archivo es el punto de partida para cualquier componente personalizado.
#   Contiene la estructura mínima obligatoria y explicaciones detalladas de cada
#   sección. Copia este archivo, renómbralo y empieza a desarrollar tu lógica.
#
# TIPOS DE COMPONENTE (tag en @HiveComponentInfo):
#   - 'collector'   : Lee datos de una fuente externa y los escribe en puerto(s)
#                     de salida (out_port). Típicamente tiene inports=0, outports≥1.
#   - 'emitter'     : Recibe datos desde Synapse y los envía a un sistema externo.
#                     Típicamente tiene inports≥1, outports=0.
#   - 'logic'       : Transforma o filtra datos entre puertos.
#   - 'action'      : Ejecuta una acción puntual (no suele escribir columnas).
#   - 'serializer'  : Serializa datos a un formato concreto (CSV, JSON, etc.).
#
# FLUJO DE EJECUCIÓN:
#   Synapse llama a los métodos en este orden cada vez que el componente se inicia:
#
#       1. premain(param)   →  Preparación / inicialización
#       2. main(param)      →  Bucle principal (corre hasta que se para el componente)
#       3. postmain(param)  →  Limpieza / liberación de recursos
#
# PARÁMETROS (param):
#   El objeto `param` que llega a premain/main/postmain contiene el JSON
#   configurado por el usuario en la interfaz de Synapse (custom_ui.json).
#   Si no se han definido parámetros todavía, llega como string vacío o None.
#
# PUERTOS:
#   - self.out_port1, self.out_port2, ...  →  puertos de salida (outports=N)
#   - self.in_port1,  self.in_port2,  ...  →  puertos de entrada (inports=N)
#   Los puertos se usan para crear columnas de datos y escribir valores en ellas.
#
# COLUMNAS DE DATOS:
#   Cada puerto de salida puede tener una o más columnas. Cada columna almacena
#   un tipo de dato concreto. Los tipos disponibles en DataType son:
#       BOOLEAN, INT8, INT16, INT32, INT64,
#       UINT8, UINT16, UINT32, UINT64,
#       FLOAT, DOUBLE, STRING, BINARY
#
# LOGGING:
#   Usa self.log.info(), self.log.warning(), self.log.error(), self.log.debug()
#   para enviar mensajes al log de Synapse (visible en el panel de componentes).
#
# ERRORES PERSONALIZADOS:
#   Se pueden definir tipos de error con ErrorType para que Synapse los muestre
#   de forma estructurada. Ver ejemplo al final de este archivo.
#
# =============================================================================

from __future__ import annotations

import random

# Importaciones base obligatorias para cualquier componente Python en Synapse.
# - HiveComponentBase  : clase base de la que hereda todo componente
# - HiveComponentInfo  : decorador que registra el componente en Synapse
# - DataType           : enumerado con los tipos de dato disponibles para columnas
# - ErrorType          : (opcional) para definir errores estructurados propios
from speedbeesynapse.component.base import (
    HiveComponentBase,
    HiveComponentInfo,
    DataType,
    ErrorType,
)

# -----------------------------------------------------------------------------
# (OPCIONAL) ERRORES PERSONALIZADOS
# -----------------------------------------------------------------------------
# Define aquí UN ErrorType por cada causa de error diferente que puede tener
# tu componente. Cada uno tiene un código que aparece en la UI de Synapse.
#
# Formato: MI_ERROR = ErrorType('CODIGO_ERROR', 'detail')
#   - 'CODIGO_ERROR' : texto corto que verá el usuario en la UI (mayúsculas)
#   - 'detail'       : nombre del campo que contendrá el mensaje de detalle
#                      (déjalo siempre como 'detail')
#
# Todos los ErrorType definidos se agrupan en una lista ERROR_TYPES que se
# pasa al decorador @HiveComponentInfo. Synapse los registra todos a la vez.
#
# Para emitir un error desde main(): return MI_ERROR('mensaje descriptivo')
# Esto para el componente y muestra el código + mensaje en la UI de Synapse.
#
# Descomenta y adapta el bloque siguiente según los errores de tu componente:
#
# MI_ERROR_CONEXION = ErrorType('CONNECTION_ERROR', 'detail')  # no se puede conectar
# MI_ERROR_TIMEOUT  = ErrorType('TIMEOUT_ERROR',    'detail')  # timeout de lectura
# MI_ERROR_LECTURA  = ErrorType('READ_ERROR',       'detail')  # fallo al leer datos
# MI_ERROR_CONFIG   = ErrorType('CONFIG_ERROR',     'detail')  # parámetros inválidos
#
# ERROR_TYPES = [                  # añade aquí TODOS los ErrorType definidos arriba
#     MI_ERROR_CONEXION,
#     MI_ERROR_TIMEOUT,
#     MI_ERROR_LECTURA,
#     MI_ERROR_CONFIG,
# ]


# -----------------------------------------------------------------------------
# CLASE DE PARÁMETROS (OPCIONAL PERO RECOMENDADO)
# -----------------------------------------------------------------------------
# Encapsula los parámetros del componente en una clase propia.
# Esto mejora la legibilidad del código y facilita añadir validaciones.
#
class Param:
    """Contenedor de parámetros del componente."""

    def __init__(self, nombre: str, intervalo_ms: int) -> None:
        self.nombre       = nombre
        self.intervalo_ns = intervalo_ms * 1_000_000  # Synapse trabaja en nanosegundos

    @staticmethod
    def parse(raw) -> 'Param':
        """Convierte el dict de parámetros de la UI en un objeto Param tipado."""
        if not isinstance(raw, dict):
            # Si no hay parámetros configurados, usa valores por defecto
            return Param(nombre='mi-componente', intervalo_ms=1000)

        return Param(
            nombre      = str(raw.get('nombre', 'mi-componente')).strip(),
            intervalo_ms= int(raw.get('intervalo_ms', 1000)),
        )


# =============================================================================
# REGISTRO DEL COMPONENTE
# =============================================================================
# El decorador @HiveComponentInfo es obligatorio. Configura cómo aparece el
# componente en la interfaz de Synapse.
#
# Parámetros del decorador:
#   uuid        : identificador único del componente. NUNCA lo cambies una vez
#                 desplegado, o Synapse lo tratará como un componente nuevo.
#                 Genera uno con: python3 -c "import uuid; print(uuid.uuid4())"
#   name        : nombre visible en la interfaz de Synapse
#   tag         : tipo de componente: 'collector', 'emitter', 'logic',
#                 'action', 'serializer'
#   inports     : número de puertos de entrada (in_port1, in_port2, ...)
#   outports    : número de puertos de salida (out_port1, out_port2, ...)
#   error_types : (opcional) lista de ErrorType propios, p.ej. ERROR_TYPES
#
@HiveComponentInfo(
    uuid     = 'a29e6f91-77a9-4ef7-a2dc-80294c8f1f41',
    name     = 'Template Component',
    tag      = 'collector',
    inports  = 0,
    outports = 1,
    # error_types = ERROR_TYPES,  # descomenta cuando hayas definido tus ErrorType arriba
)
class HiveComponent(HiveComponentBase):
    """
    Componente plantilla para SpeeDBee Synapse / DX1.

    Reemplaza esta docstring con la descripción de tu componente:
    qué hace, qué datos produce/consume y cualquier requisito previo.
    """

    # =========================================================================
    # PREMAIN — Inicialización antes del bucle principal
    # =========================================================================
    # Se ejecuta UNA SOLA VEZ al arrancar el componente, antes de main().
    # Aquí debes:
    #   - Parsear y validar los parámetros
    #   - Abrir conexiones externas (base de datos, dispositivo, API, etc.)
    #   - Crear las columnas de datos de los puertos de salida
    #   - Inicializar variables de estado internas
    #
    # IMPORTANTE: Si premain() lanza una excepción, el componente se detiene
    # inmediatamente y Synapse muestra el error. Usa try/except para errores
    # recuperables y deja que las excepciones críticas suban solas.
    #
    def premain(self, raw_param) -> None:
        # Parsear parámetros
        self._param = Param.parse(raw_param)
        p = self._param

        self.log.info(f'[{p.nombre}] premain: inicializando componente...')

        # ---------------------------------------------------------------------
        # DEFINICIÓN DE COLUMNAS DE SALIDA
        # ---------------------------------------------------------------------
        # Cada columna representa una señal/variable que el componente escribe.
        # Formato: self.<nombre_variable> = self.out_portN.Column('<nombre_col>', DataType.<TIPO>)
        #
        # El nombre de la columna es como aparecerá en la base de datos de Synapse.
        # Usa nombres descriptivos en minúsculas con guión bajo.
        #
        self.col_valor = self.out_port1.Column('valor', DataType.DOUBLE)
        # Añade más columnas según necesites:
        # self.col_estado  = self.out_port1.Column('estado',  DataType.BOOLEAN)
        # self.col_mensaje = self.out_port1.Column('mensaje', DataType.STRING)

        # ---------------------------------------------------------------------
        # INICIALIZACIÓN DE RECURSOS EXTERNOS
        # ---------------------------------------------------------------------
        # Abre aquí cualquier conexión o recurso que necesite el componente.
        # Guarda las referencias en self._ para cerrarlas en postmain().
        # Ejemplo:
        #
        # try:
        #     self._conexion = mi_libreria.connect(p.host, p.puerto)
        #     self.log.info(f'[{p.nombre}] conectado a {p.host}:{p.puerto}')
        # except Exception as e:
        #     self.log.error(f'[{p.nombre}] error de conexión: {e}')
        #     raise  # propaga el error → Synapse mostrará el fallo

        self.log.info(f'[{p.nombre}] premain: listo para iniciar')

    # =========================================================================
    # MAIN — Bucle principal del componente
    # =========================================================================
    # Se ejecuta después de premain() y corre hasta que el usuario para el
    # componente o se produce un error.
    #
    # PATRÓN BÁSICO CON while self.is_runnable():
    #   El método is_runnable() devuelve True mientras el componente debe seguir
    #   ejecutándose. Cuando el usuario lo para desde la UI, devuelve False y
    #   el bucle termina limpiamente.
    #
    # PATRÓN CON interval_iteration():
    #   interval_iteration(intervalo_ns) es el helper recomendado para bucles
    #   periódicos. Gestiona el temporizador interno de Synapse y devuelve
    #   [timestamp, skip] en cada iteración:
    #     - timestamp : marca de tiempo en nanosegundos para la inserción
    #     - skip      : True si el tick se ha retrasado (carga alta); úsalo
    #                   para omitir operaciones costosas en esos casos
    #
    # CUÁNDO USAR CADA PATRÓN:
    #   - interval_iteration() → colectores periódicos (el más habitual)
    #   - while is_runnable()  → lógica con su propio timing (eventos, callbacks,
    #                            espera de mensajes externos, etc.)
    #
    def main(self, raw_param) -> None:
        p = self._param
        self.log.info(f'[{p.nombre}] main: iniciando bucle principal')

        # -----------------------------------------------------------------------
        # OPCIÓN A — Bucle periódico con interval_iteration (RECOMENDADO para
        #            colectores que leen a intervalos fijos)
        # -----------------------------------------------------------------------
        for [ts, skip] in self.interval_iteration(p.intervalo_ns):

            if skip:
                # El tick llegó tarde (sistema bajo carga). Puedes saltar la
                # lectura costosa o simplemente seguir según tu caso de uso.
                self.log.debug(f'[{p.nombre}] tick retrasado, saltando lectura')
                continue

            # -----------------------------------------------------------------
            # AQUÍ VA TU LÓGICA DE LECTURA / PROCESADO
            # -----------------------------------------------------------------
            # Ejemplo con errores personalizados:
            #
            # try:
            #     valor = self._conexion.leer_dato()
            # except TimeoutError as e:
            #     # Error grave → para el componente y muestra "TIMEOUT_ERROR" en la UI
            #     return MI_ERROR_TIMEOUT(f'sin respuesta tras {p.timeout_s}s: {e}')
            # except Exception as e:
            #     # Error transitorio → solo log, el bucle continúa en el siguiente tick
            #     self.log.warning(f'[{p.nombre}] error de lectura: {e}')
            #     continue
            #
            # self.col_valor.insert(valor, ts)

            valor_ejemplo = random.uniform(0.0, 100.0)  # número aleatorio entre 0 y 100
            self.col_valor.insert(valor_ejemplo, ts)

        # -----------------------------------------------------------------------
        # OPCIÓN B — Bucle manual con while is_runnable() (para lógica asíncrona
        #            o con timing propio — comenta la Opción A si usas ésta)
        # -----------------------------------------------------------------------
        # import time
        # while self.is_runnable():
        #     # Tu lógica aquí
        #     time.sleep(p.intervalo_ns / 1_000_000_000)

        self.log.info(f'[{p.nombre}] main: bucle principal terminado')

    # =========================================================================
    # POSTMAIN — Limpieza al detener el componente
    # =========================================================================
    # Se ejecuta UNA SOLA VEZ después de que main() termina, tanto si fue por
    # parada manual del usuario como por un error.
    # Aquí debes:
    #   - Cerrar conexiones externas abiertas en premain()
    #   - Liberar recursos (ficheros, sockets, threads, etc.)
    #   - Escribir logs de cierre
    #
    # IMPORTANTE: postmain() se llama SIEMPRE, incluso si premain() o main()
    # fallaron. Usa try/except internamente para que los errores de limpieza
    # no enmascaren el error original.
    #
    def postmain(self, raw_param) -> None:
        p = self._param
        self.log.info(f'[{p.nombre}] postmain: liberando recursos...')

        # Cierra aquí los recursos abiertos en premain().
        # Ejemplo:
        #
        # try:
        #     if hasattr(self, '_conexion') and self._conexion:
        #         self._conexion.close()
        #         self.log.info(f'[{p.nombre}] conexión cerrada')
        # except Exception as e:
        #     self.log.warning(f'[{p.nombre}] error al cerrar conexión: {e}')

        self.log.info(f'[{p.nombre}] postmain: componente detenido correctamente')

    # =========================================================================
    # NOTIFY_STOP — Señal de parada desde Synapse (OPCIONAL)
    # =========================================================================
    # Synapse llama a notify_stop() desde un hilo distinto al de main() cuando
    # el usuario para el componente. Es útil para interrumpir operaciones
    # bloqueantes (esperas de red, lecturas de socket, etc.) sin esperar a que
    # el timeout expire.
    #
    # Si tu componente usa is_runnable() o interval_iteration(), normalmente
    # NO necesitas este método (Synapse ya gestiona la señal de parada).
    # Úsalo solo si tienes operaciones que se pueden bloquear indefinidamente.
    #
    # def notify_stop(self) -> None:
    #     self.log.info(f'[{self._param.nombre}] notify_stop: señal de parada recibida')
    #     # Interrumpe aquí operaciones bloqueantes, por ejemplo:
    #     # self._evento_parada.set()
    #     # self._conexion.interrupt()
