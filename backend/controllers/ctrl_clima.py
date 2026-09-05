import time
import board
import adafruit_dht
import RPi.GPIO as GPIO
from models.modelo_lecturas import LecturasModel, LecturaSchema
from models.modelo_eventos import EventosModel, EventoSchema

class ControladorClima:
    def __init__(self, pin_dht=board.D4, pin_ventilador=5, pin_led=6):
        # Configuración de hardware
        self.pin_ventilador = pin_ventilador
        self.pin_led = pin_led
        
        # Inicialización del Sensor DHT11 
        print("nicializando Sensor de Clima DHT11...")
        self.sensor = adafruit_dht.DHT11(pin_dht)
        
        # Variables de estado y control de errores (code del aux)
        self.max_errors = 8
        self.error_count = 0
        self.last_temperature = None
        self.last_humidity = None
        self.ultima_lectura = 0.0  # El DHT11 necesita 2 segundos entre lecturas
        self.ultima_subida = 0.0
        
        # Estado del actuador
        self.ventilador_encendido = False
        
        # Bases de datos
        self.db_lecturas = LecturasModel()
        self.db_eventos = EventosModel()
        
        # Configuración de GPIO para actuadores
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin_ventilador, GPIO.OUT)
        GPIO.setup(self.pin_led, GPIO.OUT)
        self.apagar_ventilador(forzar=True)

    def encender_ventilador(self):
        if not self.ventilador_encendido:
            print("¡Calor detectado! Encendiendo ventilador y LED azul...")
            GPIO.output(self.pin_ventilador, GPIO.HIGH)
            GPIO.output(self.pin_led, GPIO.HIGH)
            self.ventilador_encendido = True
            
            evento = EventoSchema(tipo_evento="Clima", descripcion="Ventilador encendido", severidad="INFO")
            self.db_eventos.guardar(evento)

    def apagar_ventilador(self, forzar=False):
        if self.ventilador_encendido or forzar:
            if not forzar:
                print("Temperatura estable. Apagando ventilador...")
            GPIO.output(self.pin_ventilador, GPIO.LOW)
            GPIO.output(self.pin_led, GPIO.LOW)
            self.ventilador_encendido = False
            
            if not forzar:
                evento = EventoSchema(tipo_evento="Clima", descripcion="Ventilador apagado", severidad="INFO")
                self.db_eventos.guardar(evento)

    def leer_sensor(self):
        try:
            temp = self.sensor.temperature
            hum = self.sensor.humidity

            if temp is None or hum is None:
                raise RuntimeError("Lectura nula")

            self.last_temperature = temp
            self.last_humidity = hum
            self.error_count = 0
            return temp, hum

        except RuntimeError as e:
            self.error_count += 1
            if self.last_temperature is not None and self.last_humidity is not None:
                # Usamos el último valor válido en silencio para mantener la estabilidad
                return self.last_temperature, self.last_humidity
            
            if self.error_count >= self.max_errors:
                print("Demasiados errores del DHT11. Reiniciando sensor...")
                self.sensor.exit()
                time.sleep(1) # Pausa bloqueante estrictamente necesaria para el reinicio de hardware
                self.sensor = adafruit_dht.DHT11(board.D4)
                self.error_count = 0
                
            return None, None
        except Exception as e:
            print(f"Error crítico en DHT11: {e}")
            return None, None

    def procesar(self):
        tiempo_actual = time.time()
        
        if (tiempo_actual - self.ultima_lectura) >= 2.0:
            temp, hum = self.leer_sensor()
            self.ultima_lectura = tiempo_actual
            
            if temp is not None:
                # Encendemos si pasa de 28°C, apagamos si baja de 26.5°C
                umbral_calor = 28.0
                umbral_frio = 26.5
                
                if temp >= umbral_calor:
                    self.encender_ventilador()
                elif temp <= umbral_frio:
                    self.apagar_ventilador()

                # Subida de datos a MongoDB (Cada 10 segundos)
                if (tiempo_actual - self.ultima_subida) >= 10.0:
                    print(f"Clima: {temp:.1f}°C | Humedad: {hum:.1f}%")
                    
                    # Guardamos ambas lecturas (Temperatura y Humedad)
                    lec_temp = LecturaSchema(sensor="DHT11_Sala", tipo="temperatura", valor=temp, unidad="C")
                    lec_hum = LecturaSchema(sensor="DHT11_Sala", tipo="humedad", valor=hum, unidad="%")
                    self.db_lecturas.guardar(lec_temp)
                    self.db_lecturas.guardar(lec_hum)
                    
                    self.ultima_subida = tiempo_actual

if __name__ == "__main__":
    clima = ControladorClima()
    try:
        while True:
            clima.procesar()
            time.sleep(0.1) 
    except KeyboardInterrupt:
        print("\nPrueba finalizada por el usuario.")
    finally:
        clima.sensor.exit()
        clima.apagar_ventilador(forzar=True)
        GPIO.cleanup()
