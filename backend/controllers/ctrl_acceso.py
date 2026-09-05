import time
import statistics
import RPi.GPIO as GPIO
from models.modelo_lecturas import LecturasModel, LecturaSchema
from models.modelo_eventos import EventosModel, EventoSchema

class ControladorAcceso:
    def __init__(self, pin_trigger=23, pin_echo=24, pin_servo=12):
        # Configuración de pines
        self.pin_trigger = pin_trigger
        self.pin_echo = pin_echo
        self.pin_servo = pin_servo
        
        # Conexiones a Base de Datos
        self.db_lecturas = LecturasModel()
        self.db_eventos = EventosModel()
        self.ultima_subida = 0  
        
        # Constantes físicas ultrasónico
        self.speed_of_sound = 34300
        self.timeout = 0.02
        self.samples = 5

        # Estado de la Puerta
        self.puerta_abierta = False
        self.tiempo_apertura = 0.0

        # Inicialización de GPIO
        print(f"Inicializando Acceso (TRIG:{pin_trigger} ECHO:{pin_echo} SERVO:{pin_servo})...")
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin_trigger, GPIO.OUT)
        GPIO.setup(self.pin_echo, GPIO.IN)
        
        # Inicialización del Servomotor (50Hz)
        GPIO.setup(self.pin_servo, GPIO.OUT)
        self.pwm_servo = GPIO.PWM(self.pin_servo, 50)
        self.pwm_servo.start(0)
        
        # Cerramos la puerta al arrancar el sistema
        self.cerrar_puerta(forzar=True)

    def abrir_puerta(self):
        print("Abriendo puerta ...")
        duty = 2.5
        # Barrido suave de 0° (2.5) a 90° (7.5)
        while duty <= 7.5:
            self.pwm_servo.ChangeDutyCycle(duty)
            time.sleep(0.05)
            duty += 0.5
            
        self.pwm_servo.ChangeDutyCycle(0) # Descanso del motor
        self.puerta_abierta = True
        self.tiempo_apertura = time.time()
        
        # Registrar evento en MongoDB Atlas
        evento = EventoSchema(tipo_evento="Acceso", descripcion="Puerta principal abierta", severidad="INFO")
        self.db_eventos.guardar(evento)

    def cerrar_puerta(self, forzar=False):
        if self.puerta_abierta or forzar:
            if not forzar:
                print("Cerrando puerta automáticamente...")
            
            duty = 7.5
            # Barrido suave de 90° (7.5) de regreso a 0° (2.5)
            while duty >= 2.5:
                self.pwm_servo.ChangeDutyCycle(duty)
                time.sleep(0.05)
                duty -= 0.5
                
            self.pwm_servo.ChangeDutyCycle(0)
            self.puerta_abierta = False
            
            # Registrar evento en MongoDB Atlas (solo si fue un cierre normal)
            if not forzar:
                evento = EventoSchema(tipo_evento="Acceso", descripcion="Puerta principal cerrada", severidad="INFO")
                self.db_eventos.guardar(evento)

    def _leer_pulso(self):
        #Lógica del sensor HC-SR04
        GPIO.output(self.pin_trigger, GPIO.LOW)
        time.sleep(0.0002)
        GPIO.output(self.pin_trigger, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self.pin_trigger, GPIO.LOW)

        start_time = time.time()
        while GPIO.input(self.pin_echo) == GPIO.LOW:
            if time.time() - start_time > self.timeout:
                return None

        pulse_start = time.time()
        while GPIO.input(self.pin_echo) == GPIO.HIGH:
            if time.time() - pulse_start > self.timeout:
                return None

        pulse_end = time.time()
        return ((pulse_end - pulse_start) * self.speed_of_sound) / 2

    def leer_distancia_mediana(self):
        #Filtro de ruido con la mediana
        muestras = []
        for _ in range(self.samples):
            valor = self._leer_pulso()
            if valor is not None:
                muestras.append(valor)
            time.sleep(0.05)
        return statistics.median(muestras) if muestras else None

    def procesar(self):
        distancia = self.leer_distancia_mediana()
        tiempo_actual = time.time()

        if distancia is not None:
            # Evaluar si alguien está cerca para abrir la puerta
            if distancia < 10.0 and not self.puerta_abierta:
                self.abrir_puerta()
            
            # Cerrar la puerta automáticamente tras 5 segundos
            elif self.puerta_abierta and (tiempo_actual - self.tiempo_apertura) >= 5.0:
                self.cerrar_puerta()

            # Subir la lectura a MongoDB Atlas cada 3 segundos
            if (tiempo_actual - self.ultima_subida) >= 3.0:
                # Imprimimos en consola solo cada 3 segundos 
                print(f"Distancia actual: {distancia:.1f} cm")
                
                lectura = LecturaSchema(
                    sensor="HC-SR04_Entrada", 
                    tipo="distancia", 
                    valor=round(distancia, 2), 
                    unidad="cm"
                )
                self.db_lecturas.guardar(lectura)
                self.ultima_subida = tiempo_actual

# ZONA DE PRUEBA INDEPENDIENTE
if __name__ == "__main__":
    acceso = ControladorAcceso()
    try:
        while True:
            acceso.procesar()
            time.sleep(0.1) 
    except KeyboardInterrupt:
        print("\nPrueba finalizada por el usuario.")
    finally:
        acceso.cerrar_puerta(forzar=True)
        time.sleep(0.5)
        GPIO.cleanup()
