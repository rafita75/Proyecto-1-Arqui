import time

# Importamos todos los Modelos y sus Schemas estrictos
from models.modelo_lecturas import LecturasModel, LecturaSchema
from models.modelo_eventos import EventosModel, EventoSchema
from models.modelo_comandos import ComandosModel, ComandoSchema
from models.modelo_estado import EstadoModel, EstadoSchema
from models.modelo_arm64 import Arm64Model, Arm64Schema

print("🔄 Iniciando prueba global de envíos a MongoDB Atlas...\n")

try:
    # 1. Prueba de LECTURAS (Sensores)
    print("Enviando Lectura...")
    db_lecturas = LecturasModel()
    prueba_sensor = LecturaSchema(sensor="DHT11_Prueba", tipo="temperatura", valor=25.5, unidad="C")
    db_lecturas.guardar(prueba_sensor)

    # 2. Prueba de EVENTOS (Alertas)
    print("Enviando Evento...")
    db_eventos = EventosModel()
    prueba_evento = EventoSchema(tipo_evento="Prueba de Sistema", descripcion="Validando conexión", severidad="INFO")
    db_eventos.guardar(prueba_evento)

    # 3. Prueba de COMANDOS (Dashboard remoto)
    print("Enviando Comando...")
    db_comandos = ComandosModel()
    prueba_comando = ComandoSchema(actuador="Luces_Sala", accion="Encender", origen="Script de Prueba")
    db_comandos.guardar(prueba_comando)

    # 4. Prueba de ESTADO GLOBAL (LEDs semáforo)
    print("Enviando Estado Global...")
    db_estado = EstadoModel()
    prueba_estado = EstadoSchema(estado_global="NORMAL", motivo="Inicialización correcta")
    db_estado.guardar(prueba_estado)

    # 5. Prueba de RESULTADOS ARM64 (Fase de Ensamblador)
    print("Enviando Resultados de Ensamblador...")
    db_arm64 = Arm64Model()
    prueba_arm = Arm64Schema(maximo=35.0, minimo=12.0, promedio=23.4, total_datos=20, tiempo_ms=1.5)
    db_arm64.guardar(prueba_arm)

    print("\n🚀 ¡Todas las pruebas finalizadas!")
    print("Ve a tu clúster en Atlas y verifica que tu base de datos 'edificio_inteligente' tenga las 5 colecciones con sus datos.")

except Exception as e:
    print(f"\n❌ Ocurrió un error crítico durante la ejecución: {e}")
