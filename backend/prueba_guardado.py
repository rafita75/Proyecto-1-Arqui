from models.modelo_lecturas import LecturasModel, LecturaSchema
from models.modelo_eventos import EventosModel, EventoSchema

# db = LecturasModel()

# print("Generando lectura de prueba...")

# lectura_prueba = LecturaSchema(
#     sensor="HC-SR04-PRUEBA",
#     tipo="distancia",
#     valor=42.5,
#     unidad="cm"
# )

# db.guardar(lectura_prueba)

db = EventosModel()
print("Generando evento de prueba...")
evento_prueba = EventoSchema(
	tipo_evento = "Alerta de gas",
	descripcion = "Nivel demasiado alto de gas",
	severidad = "EMERGENCIA"
)

db.guardar(evento_prueba)
