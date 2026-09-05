import os
import time
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

@dataclass
class Arm64Schema:
    maximo: float
    minimo: float
    promedio: float
    total_datos: int
    tiempo_ms: float     # Para tu punto extra de comparación de rendimiento
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

class Arm64Model:
    def __init__(self):
        uri = os.getenv("MONGO_URI")
        self.coleccion = MongoClient(uri)["proyecto1"]["arm64"]

    def guardar(self, datos: Arm64Schema):
        try:
            resultado = self.coleccion.insert_one(asdict(datos))
            print(f"✅ [Atlas] Estadistica guardada con ID: {resultado.inserted_id}")
            return resultado.inserted_id
        except Exception as e:
            print(f"❌ Error al guardar resultados ARM64: {e}")
            return None
