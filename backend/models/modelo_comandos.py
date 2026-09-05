import os
import time
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

@dataclass
class ComandoSchema:
    actuador: str        # "Servomotor", "Luces", "Ventilador"
    accion: str          # "Abrir", "Encender", "Apagar"
    origen: str          # "Dashboard Web", "Botón Físico"
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

class ComandosModel:
    def __init__(self):
        uri = os.getenv("MONGO_URI")
        self.coleccion = MongoClient(uri)["proyecto1"]["comandos"]

    def guardar(self, datos: ComandoSchema):
        try:
            resultado = self.coleccion.insert_one(asdict(datos))
            print(f"✅ [Atlas] Comando guardado con ID: {resultado.inserted_id}")
            return resultado.inserted_id
        except Exception as e:
            print(f"❌ Error al guardar comando: {e}")
            return None
