"""Reglas de validación del alta de un animal."""
from app.core.excepciones import ErrorApi
from app.services.animales.fechas import hoy


ESTADOS_ALTA = ("en_produccion", "seco", "no_productivo")


def _validar_alta(c: dict) -> dict:
    errores, v = {}, {}

    def texto(campo, maximo, obligatorio=True):
        valor = (c.get(campo) or "").strip()
        if not valor:
            if obligatorio:
                errores[campo] = "Este campo es obligatorio."
            v[campo] = None
        elif len(valor) > maximo:
            errores[campo] = f"Máximo {maximo} caracteres."
        else:
            v[campo] = valor

    texto("arete", 40)
    texto("raza", 80)
    texto("procedencia", 160)
    texto("nombre", 100, obligatorio=False)
    if v.get("arete"):
        v["arete"] = v["arete"].upper()  # trim + mayúsculas: no distingue mayúsculas

    limite = hoy()
    ingreso, nacimiento, edad = c.get("fecha_ingreso"), c.get("fecha_nacimiento"), c.get("edad_estimada_meses")
    if ingreso is None:
        errores["fecha_ingreso"] = "Este campo es obligatorio."
    elif ingreso > limite:
        errores["fecha_ingreso"] = "No puede ser una fecha futura."
    if (nacimiento is None) == (edad is None):
        mensaje = "Envía la fecha de nacimiento o la edad estimada, pero no ambas ni ninguna."
        errores["fecha_nacimiento"] = errores["edad_estimada_meses"] = mensaje
    elif nacimiento is not None:
        if nacimiento > limite:
            errores["fecha_nacimiento"] = "No puede ser una fecha futura."
        elif ingreso is not None and nacimiento > ingreso:
            errores["fecha_nacimiento"] = "No puede ser posterior a la fecha de ingreso."
    elif edad < 0:
        errores["edad_estimada_meses"] = "Debe ser 0 o mayor."
    if c.get("estado_inicial") not in ESTADOS_ALTA:
        errores["estado_inicial"] = "Usa en_produccion, seco o no_productivo."
    if errores:
        raise ErrorApi(422, "VALIDACION", "Revisa los campos indicados.", errores)
    v.update(fecha_ingreso=ingreso, fecha_nacimiento=nacimiento, edad_estimada_meses=edad,
             estado_inicial=c["estado_inicial"])
    return v
