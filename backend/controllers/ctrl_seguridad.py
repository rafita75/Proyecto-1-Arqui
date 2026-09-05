import time
import RPi.GPIO as GPIO
import smbus2
from models.modelo_lecturas import LecturasModel, LecturaSchema
from models.modelo_eventos import EventosModel, EventoSchema

class ControladorSeguridad:
    def __init__(self, pin_led_rojo=26, pin_buzzer=16):
        self.pin_led_rojo = pin_led_rojo
        self.pin_buzzer = pin_buzzer
        
        # Configuración I2C (PCF8591)
        self.i2c_port = 1
        self.i2c_addr = 0x48
        
        try:
            self.bus = smbus2.SMBus(self.i2c_port)
            print("Módulo de Seguridad I2C conectado.")
        except Exception as e:
            print(f"Error I2C en Seguridad: {e}")
            self.bus = None

        # Bases de Datos y Tiempos
        self.db_lecturas = LecturasModel()
        self.db_eventos = EventosModel()
        self.ultima_subida = 0.0
        
        # Estado de Alarma
        self.alarma_activada = False
        
        # Inicializar GPIO 
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin_led_rojo, GPIO.OUT)
        GPIO.setup(self.pin_buzzer, GPIO.OUT)
        self.desactivar_alarma(forzar=True)

    def leer_gas(self):
        if self.bus is None:
            print("Bus I2C no inicializado. No se puede leer el sensor MQ-2.")
            return None
            
        try:
            # 0x41 es el comando para leer AIN1
            self.bus.write_byte(self.i2c_addr, 0x41)
            self.bus.read_byte(self.i2c_addr) # Lectura basura a descartar
            valor = self.bus.read_byte(self.i2c_addr)
            return valor
        except Exception as e:
            print(f"Error leyendo MQ-2: {e}")
            return None

    def activar_alarma(self):
        if not self.alarma_activada:
            print("¡ALERTA CRÍTICA! Fuga de gas detectada. Activando alarmas...")
            GPIO.output(self.pin_led_rojo, GPIO.HIGH)
            GPIO.output(self.pin_buzzer, GPIO.HIGH)
            self.alarma_activada = True
            
            # Registrar evento de máxima prioridad
            evento = EventoSchema(tipo_evento="Emergencia", descripcion="Alto nivel de gas detectado", severidad="CRÍTICA")
            self.db_eventos.guardar(evento)

    def desactivar_alarma(self, forzar=False):
        if self.alarma_activada or forzar:
            if not forzar:
                print("Niveles de gas normalizados. Apagando alarmas.")
            GPIO.output(self.pin_led_rojo, GPIO.LOW)
            GPIO.output(self.pin_buzzer, GPIO.LOW)
            self.alarma_activada = False

            if not forzar:
                evento = EventoSchema(tipo_evento="Seguridad", descripcion="Sistema estabilizado", severidad="INFO")
                self.db_eventos.guardar(evento)

    def procesar(self):
        nivel_gas = self.leer_gas()
        tiempo_actual = time.time()
        estado_global = "NORMAL"

        if nivel_gas is not None:
            # Umbrales (De 0 a 255)
            umbral_peligro = 180
            umbral_seguro = 100
            
            if nivel_gas > umbral_peligro:
                self.activar_alarma()
                estado_global = "EMERGENCIA"
            elif nivel_gas < umbral_seguro:
                self.desactivar_alarma()
                estado_global = "NORMAL"
            elif self.alarma_activada:
                estado_global = "EMERGENCIA" # Mantiene el estado hasta que baje al nivel seguro

            # Subir lecturas a MongoDB cada 5 segundos
            if (tiempo_actual - self.ultima_subida) >= 5.0:
                print(f"Nivel de gas: {nivel_gas}/255")
                lectura = LecturaSchema(sensor="MQ2_Cocina", tipo="gas", valor=nivel_gas, unidad="ADC")
                self.db_lecturas.guardar(lectura)
                self.ultima_subida = tiempo_actual
                
        # Devolvemos el estado para que el main.py sepa qué hacer con la puerta
        return estado_global


if __name__ == "__main__":
    seguridad = ControladorSeguridad()
    try:
        while True:
            estado = seguridad.procesar()
            if estado == "EMERGENCIA":
                print("[Notificación al Main] Se debe forzar la apertura de la puerta.")
            time.sleep(0.5) 
    except KeyboardInterrupt:
        print("\nPrueba finalizada por el usuario.")
    finally:
        seguridad.desactivar_alarma(forzar=True)
        GPIO.cleanup()
