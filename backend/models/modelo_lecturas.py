import os
import time
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

@dataclass
class LecturaSchema:
    sensor: str
    tipo: str
    valor: float
    unidad: str
    timestamp: float = 0.0

    def __post_init__(self):
        # Asigna el tiempo actual automáticamente si no se envía uno
        if self.timestamp == 0.0:
            self.timestamp = time.time()

class LecturasModel:
    def __init__(self):
        uri = os.getenv("MONGO_URI")
        self.cliente = MongoClient(uri)
        self.db = self.cliente["proyecto1"] 
        self.coleccion = self.db["sensores"]

    def guardar(self, datos: LecturaSchema):
        try:
            # asdict() transforma la clase en un objeto JSON compatible con Mongo
            documento = asdict(datos)
            resultado = self.coleccion.insert_one(documento)
            print(f"✅ [Atlas] Registro guardado con ID: {resultado.inserted_id}")
            return True
        except Exception as e:
            print(f"❌ [Atlas] Error de conexión: {e}")
            return False
