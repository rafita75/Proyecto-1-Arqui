import os
import time
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

@dataclass
class EstadoSchema:
    estado_global: str   # "NORMAL", "ADVERTENCIA", "EMERGENCIA"
    motivo: str          # "Todo en orden", "Temperatura alta"
    puerta_abierta: bool
    ventilador_encendido: bool
    luces_encendidas: bool
    alarma_activa: bool
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

class EstadoModel:
    def __init__(self):
        uri = os.getenv("MONGO_URI")
        self.coleccion = MongoClient(uri)["proyecto1"]["estados"]

    def guardar(self, datos: EstadoSchema):
        try:
            resultado = self.coleccion.insert_one(asdict(datos))
            print(f"✅ [Atlas] Estado guardado con ID: {resultado.inserted_id}")
            return resultado.inserted_id
        except Exception as e:
            print(f"Error al guardar estado: {e}")
            return None
