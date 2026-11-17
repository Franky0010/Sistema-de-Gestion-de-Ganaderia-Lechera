"""Unidad de trabajo EN MEMORIA que implementa los puertos de app/services/puertos.py.

Permite probar las reglas de negocio de los servicios sin SQLite ni SQLAlchemy Session.
Imita lo esencial de la base: ids autoincrementales, restricciones únicas al hacer flush
(lanzan ErrorIntegridad como la capa real) y rollback que deshace altas y modificaciones.
"""
from app.core.excepciones import ErrorIntegridad


def _atributos(entidad):
    """Copia de los atributos de datos de una entidad (sin el estado interno de SQLAlchemy)."""
    return {k: v for k, v in entidad.__dict__.items() if not k.startswith("_")}


class _Almacen:
    def __init__(self):
        self.confirmados = {k: [] for k in ("usuarios", "sesiones", "animales", "estados", "ordenos", "auditoria")}
        self.pendientes = []            # (tabla, entidad) aún sin confirmar
        self.foto = {}                  # id(entidad) -> copia de __dict__ al último commit
        self._ids = {k: 0 for k in self.confirmados}

    def todos(self, tabla):
        return self.confirmados[tabla] + [e for t, e in self.pendientes if t == tabla]


class _Repo:
    tabla = ""

    def __init__(self, almacen):
        self._a = almacen

    def agregar(self, entidad):
        self._a.pendientes.append((self.tabla, entidad))

    def _todos(self):
        return self._a.todos(self.tabla)


class RepoUsuarios(_Repo):
    tabla = "usuarios"

    def obtener(self, usuario_id):
        return next((u for u in self._todos() if u.id == usuario_id), None)

    def obtener_por_email(self, email):
        return next((u for u in self._todos() if u.email == email), None)

    def buscar(self, texto, page, page_size):
        t = texto.strip().lower()
        fil = [u for u in self._todos() if not t or t in u.nombre.lower() or t in u.email.lower()]
        fil.sort(key=lambda u: u.id)
        return fil[(page - 1) * page_size: page * page_size], len(fil)

    def contar_administradores_activos(self):
        return sum(1 for u in self._todos() if u.rol == "administrador" and u.activo)


class RepoSesiones(_Repo):
    tabla = "sesiones"

    def obtener_con_usuario(self, hash_token):
        for s in self._todos():
            if s.hash_token == hash_token:
                return s, next(u for u in self._a.todos("usuarios") if u.id == s.usuario_id)
        return None

    def revocar_activas_de(self, usuario_id, instante):
        for s in self._todos():
            if s.usuario_id == usuario_id and s.revocada_en is None:
                s.revocada_en = instante


class RepoAnimales(_Repo):
    tabla = "animales"

    def obtener(self, animal_id):
        return next((a for a in self._todos() if a.id == animal_id), None)

    def incrementar_version(self, animal_id, version_esperada):
        animal = self.obtener(animal_id)
        if animal is None or animal.version != version_esperada:
            return False
        animal.version += 1
        return True


class RepoEstados(_Repo):
    tabla = "estados"

    def _de(self, animal_id):
        return sorted((e for e in self._todos() if e.animal_id == animal_id), key=lambda e: (e.fecha_desde, e.id))

    def vigente_en(self, animal_id, fecha):
        previos = [e for e in self._de(animal_id) if e.fecha_desde <= fecha]
        return previos[-1] if previos else None

    def siguiente_a(self, animal_id, fecha):
        return next((e for e in self._de(animal_id) if e.fecha_desde > fecha), None)

    def listar(self, animal_id, page, page_size):
        filas = self._de(animal_id)
        return filas[(page - 1) * page_size: page * page_size], len(filas)

    def tiene_estado(self, animal_id, estado):
        return any(e.estado == estado for e in self._de(animal_id))

    def existe_cambio_en(self, animal_id, fecha):
        return any(e.fecha_desde == fecha for e in self._de(animal_id))


class RepoOrdenos(_Repo):
    tabla = "ordenos"

    def hay_vigentes(self, animal_id, desde, hasta=None):
        return any(o.animal_id == animal_id and not o.anulado and o.fecha >= desde
                   and (hasta is None or o.fecha < hasta) for o in self._todos())


class RepoAuditoria(_Repo):
    tabla = "auditoria"

    def buscar(self, *, entidad, entidad_id, accion, usuario_id, page, page_size):
        fil = [a for a in self._todos()
               if (not entidad or a.entidad == entidad) and (entidad_id is None or a.entidad_id == entidad_id)
               and (not accion or a.accion == accion) and (usuario_id is None or a.usuario_id == usuario_id)]
        fil.sort(key=lambda a: -a.id)
        return fil[(page - 1) * page_size: page * page_size], len(fil)


class UnidadDeTrabajoMemoria:
    def __init__(self):
        self._a = _Almacen()
        self.usuarios, self.sesiones = RepoUsuarios(self._a), RepoSesiones(self._a)
        self.animales, self.estados = RepoAnimales(self._a), RepoEstados(self._a)
        self.ordenos, self.auditoria = RepoOrdenos(self._a), RepoAuditoria(self._a)

    # ---- restricciones únicas que en producción impone SQLite
    def _validar_unicos(self):
        reglas = {"usuarios": ("email",), "animales": ("arete",),
                  "estados": ("animal_id", "fecha_desde"), "ordenos": ("animal_id", "fecha", "turno")}
        for tabla, campos in reglas.items():
            vistos = set()
            for e in self._a.todos(tabla):
                clave = tuple(getattr(e, c) for c in campos)
                if clave in vistos:
                    raise ErrorIntegridad(f"UNIQUE constraint failed: {tabla}.{', '.join(campos)}"
                                          .replace("usuarios.", "usuario.").replace("animales.", "animal."))
                vistos.add(clave)

    def flush(self):
        for tabla, entidad in self._a.pendientes:
            if getattr(entidad, "id", None) is None:
                self._a._ids[tabla] += 1
                entidad.id = self._a._ids[tabla]
        self._validar_unicos()

    def commit(self):
        self.flush()
        for tabla, entidad in self._a.pendientes:
            self._a.confirmados[tabla].append(entidad)
        self._a.pendientes.clear()
        self._a.foto = {id(e): _atributos(e) for lista in self._a.confirmados.values() for e in lista}

    def rollback(self):
        self._a.pendientes.clear()
        for lista in self._a.confirmados.values():
            for e in lista:
                for nombre, valor in self._a.foto.get(id(e), {}).items():
                    setattr(e, nombre, valor)

    def refrescar(self, entidad):
        pass

    # ---- ayudas para las pruebas
    def confirmados(self, tabla):
        return list(self._a.confirmados[tabla])
