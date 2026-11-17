"""Representación pública de estados y snapshots para la auditoría."""
from app.models import Animal, EstadoAnimal


def _iso(valor):
    return valor.isoformat() if valor is not None else None


def snapshot(a: Animal, estado: str | None = None) -> dict:
    datos = {"arete": a.arete, "nombre": a.nombre, "raza": a.raza, "procedencia": a.procedencia,
             "fecha_ingreso": _iso(a.fecha_ingreso), "fecha_nacimiento": _iso(a.fecha_nacimiento),
             "edad_estimada_meses": a.edad_estimada_meses, "version": a.version}
    if estado:
        datos["estado"] = estado
    return datos


def estado_publico(e: EstadoAnimal) -> dict:
    return {"id": e.id, "animal_id": e.animal_id, "estado": e.estado,
            "fecha_desde": _iso(e.fecha_desde), "motivo": e.motivo, "responsable_id": e.responsable_id}
