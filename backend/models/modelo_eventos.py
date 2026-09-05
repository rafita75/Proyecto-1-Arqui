import os
import time
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

@dataclass
class EventoSchema:
    tipo_evento: str     # "Alerta de Gas", "Puerta Forzada"
    descripcion: str     # "Nivel de gas superó los 300ppm"
    severidad: str       # "ADVERTENCIA", "EMERGENCIA", "INFO"
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

class EventosModel:
    def __init__(self):
        uri = os.getenv("MONGO_URI")
        self.coleccion = MongoClient(uri)["proyecto1"]["eventos"]

    def guardar(self, datos: EventoSchema):
        try:
            resultado = self.coleccion.insert_one(asdict(datos))
            print(f"✅ [Atlas] Evento guardado con ID: {resultado.inserted_id}")
            return resultado.inserted_id
        except Exception as e:
            print(f"❌ Error al guardar evento: {e}")
            return None
