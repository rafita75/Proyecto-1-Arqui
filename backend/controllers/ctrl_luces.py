import time
import RPi.GPIO as GPIO
import smbus2
from models.modelo_lecturas import LecturasModel, LecturaSchema
from models.modelo_eventos import EventosModel, EventoSchema

class ControladorLuces:
    def __init__(self, pines_leds=[21, 18, 14]):
        self.pines_leds = pines_leds
        
        # Base de datos y variables de tiempo
        self.db_lecturas = LecturasModel()
        self.db_eventos = EventosModel()
        self.ultima_subida = 0.0
        
        # Estado del sistema
        self.luces_encendidas = False
        
        # Configuración del Bus I2C (PCF8591)
        self.i2c_port = 1
        self.i2c_addr = 0x48  
        
        try:
            self.bus = smbus2.SMBus(self.i2c_port)
            print(f"Módulo I2C (LDR) conectado en {hex(self.i2c_addr)}.")
        except Exception as e:
            print(f"Error I2C: {e}")
            self.bus = None

        # Inicialización de los 3 GPIOs para los LEDs
        print(f"LEDs configurados en los pines GPIO: {self.pines_leds}")
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        for pin in self.pines_leds:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

    def leer_luminosidad(self):
        if self.bus is None:
            print("No se puede leer la LDR. Bus I2C desconectado.")
            return None
        
        try:
            self.bus.write_byte(self.i2c_addr, 0x40)
            self.bus.read_byte(self.i2c_addr) # Limpiar buffer
            valor_real = self.bus.read_byte(self.i2c_addr)
            return valor_real
        except Exception as e:
            print(f"Error de hardware leyendo el ADC: {e}")
            return None

    def encender_luces(self):
        if not self.luces_encendidas:
            print("Oscuridad detectada. Encendiendo los 3 LEDs exteriores...")
            for pin in self.pines_leds:
                GPIO.output(pin, GPIO.HIGH)
            self.luces_encendidas = True
            
            evento = EventoSchema(tipo_evento="Iluminación", descripcion="Luces automáticas encendidas", severidad="INFO")
            self.db_eventos.guardar(evento)

    def apagar_luces(self):
        if self.luces_encendidas:
            print("Luz de día detectada. Apagando LEDs...")
            for pin in self.pines_leds:
                GPIO.output(pin, GPIO.LOW)
            self.luces_encendidas = False
            
            evento = EventoSchema(tipo_evento="Iluminación", descripcion="Luces automáticas apagadas", severidad="INFO")
            self.db_eventos.guardar(evento)

    def procesar(self):
        luz = self.leer_luminosidad()
        tiempo_actual = time.time()

        if luz is not None:
            umbral_encender = 180
            umbral_apagar = 130
            
            if luz > umbral_encender:
                self.encender_luces()
            elif luz < umbral_apagar:
                self.apagar_luces()

            if (tiempo_actual - self.ultima_subida) >= 5.0:
                print(f"Nivel de luz actual: {luz}/255")
                lectura = LecturaSchema(sensor="LDR_Exterior", tipo="luminosidad", valor=luz, unidad="ADC")
                self.db_lecturas.guardar(lectura)
                self.ultima_subida = tiempo_actual


if __name__ == "__main__":
    luces = ControladorLuces()
    try:
        while True:
            luces.procesar()
            time.sleep(0.5) 
    except KeyboardInterrupt:
        print("\nPrueba finalizada por el usuario.")
    finally:
        luces.apagar_luces()
        time.sleep(0.1)
        GPIO.cleanup()
