# Contrato API — Sprint 1

**Estado: implementado en el backend para sesión/CSRF, usuarios, auditoría y registro y estados de animales; pendiente de aprobación del equipo. Falta `GET /animales` (lista, PB-04).**
Vinculado a PB-01, PB-02, PB-03, PB-04, PB-11, HT-01 y HT-02.

### Estado de implementación (backend)

| Bloque                                                                          | Estado                                              | Código                                                 |
| ------------------------------------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------ |
| Sesión y CSRF                                                                   | Implementado                                        | `rutas_auth.py`, `servicio_auth.py`, `dependencias.py` |
| Usuarios                                                                        | Implementado (incluye `motivo` al cambiar `activo`) | `rutas_usuarios.py`, `servicio_usuarios.py`            |
| Auditoría (consulta y protección)                                               | Implementado                                        | `auditoria.py`, `rutas_auditoria.py`                   |
| Animales: `POST /animales`, `GET /animales/{id}`, `POST /animales/{id}/estados` | Implementado                                        | `rutas_animales.py`, `servicio_animales.py`            |
| Animales: `GET /animales` (lista, búsqueda, filtro por estado)                  | **Pendiente** (PB-04)                               | —                                                      |
| Respaldo y restauración                                                         | Implementado (script)                               | `respaldo.py`                                          |

## Responsables según las subtareas de GitHub

| Responsable                         | Alcance                                                                                         | Subtareas               |
| ----------------------------------- | ----------------------------------------------------------------------------------------------- | ----------------------- |
| Juan Diego Loaiza (@Juanloaiza25)   | Frontend de acceso, usuarios, navegación por rol, registro de animales y cambios de estado      | #26, #28, #30, #32, #34 |
| Franky Marin (@Franky0010)          | Backend de sesión, usuarios, permisos por rol y seguridad; integridad y auditoría de usuarios   | #27, #29, #31, #36, #38 |
| Juan Manuel Alvarez (@juanalvarez6) | Backend de registro de animales, estados e historial; base compartida de integridad y auditoría | #33, #35, #37           |

Franky integra la auditoría de usuarios con la base compartida a cargo de Juan Manuel. Este reparto refleja las asignaciones consultadas en GitHub el 2 de noviembre de 2026.

## Decisiones comunes

- Base `/api/v1`. JSON UTF-8; nombres de campos en español. Identificadores enteros positivos.
- La UI y la API comparten origen. Vite redirige `/api` al FastAPI local en desarrollo. Producción: HTTPS obligatorio.
- El PoC conserva `POST /animales` y `POST /ordenos`. **No conectar los formularios nuevos al `/animales` antiguo:** acepta datos insuficientes. Crear rutas versionadas completas.
- Fechas de negocio `YYYY-MM-DD`, zona America/Bogota, sin convertirlas a UTC. Auditoría: instantes ISO 8601 UTC.
- Listas: `{ "items": [...], "total": 42, "page": 1, "page_size": 20 }`. Parámetros `page` (>=1), `page_size` (1..100), `search` (texto opcional). Orden estable por ID ascendente. Filtrar antes de paginar.
- Roles exactos: `administrador`, `operario`, `propietario`. Estados: `en_produccion`, `seco`, `no_productivo`, `fuera_del_hato`.
- El servidor valida todos los datos y permisos. No aceptar usuario/responsable/fecha de auditoría enviados por la UI. No borrar datos históricos.
- No hay reintentos automáticos de escrituras. Ante pérdida de respuesta, consultar antes de repetir. La unicidad debe ser transaccional.
- Toda escritura es una sola transacción: datos, efectos asociados (versión, estado inicial) y auditoría se confirman o se revierten juntos. Si algo falla antes del commit no queda nada guardado.
- Las claves foráneas están activas en la base de datos. Una violación que ningún servicio traduzca se responde con un error del contrato (`REFERENCIA_INVALIDA`, `DUPLICADO`, `CONFLICTO_DATOS`), nunca con un 500 ni con SQL.
- Motivo obligatorio (máx. 500) en correcciones, anulaciones, reactivaciones y cambios de estado, incluido desactivar un usuario. Se valida antes de escribir.
- Un método no permitido responde 405 `METODO_NO_PERMITIDO`.

## Sesión y CSRF — Franky Marin (@Franky0010)

Cookie de sesión opaca `sesion`, HttpOnly, Secure en HTTPS, SameSite=Lax, Path=/. No devolver el token de sesión en JSON ni almacenarlo en localStorage. Timeout de 30 minutos de inactividad en servidor; invalidar al cerrar sesión o desactivar usuario. Verificar rol y estado vigente en cada petición. Respuestas de sesión y CSRF con `Cache-Control: no-store`.

| Método/ruta         | Entrada                                                             | Respuesta                                                                                                |
| ------------------- | ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| GET `/auth/csrf`    | Ninguna                                                             | 200 `{ "csrf_token": "token-opaco" }`; establecer cookie anónima ligada al token cuando no exista sesión |
| GET `/auth/session` | Cookie                                                              | 200 `{ "usuario": Usuario }`; 401 si no hay sesión válida                                                |
| POST `/auth/login`  | `{ "email": "admin@finca.co", "password": "..." }` + `X-CSRF-Token` | 200 `{ "usuario": Usuario, "csrf_token": "nuevo-token" }`; rotar ID de sesión y CSRF                     |
| POST `/auth/logout` | Cookie + `X-CSRF-Token`, sin cuerpo                                 | 204; revocar sesión y borrar cookie                                                                      |

Todas las escrituras, incluido login/logout, verifican origen y CSRF antes de escribir. GET CSRF entrega un token ligado a la sesión actual, no rota la sesión ni prolonga artificialmente su vigencia. El frontend solicita CSRF antes de cada escritura; no hace polling para mantener la sesión viva.

Usuario público: `{ "id": 1, "nombre": "Ana Pérez", "email": "ana@finca.co", "rol": "administrador", "activo": true }`.

Error de login incorrecto: 401 `CREDENCIALES_INVALIDAS`. Cuenta inactiva: 403 `CUENTA_INACTIVA` **solo después de verificar contraseña**; no revelar si existe una cuenta mediante una contraseña incorrecta. Sesión caducada/revocada: 401 `SESION_EXPIRADA`. El cliente limpia datos de pantallas privadas y vuelve al acceso. Prohibido registrar contraseñas, cookies o tokens en logs.

## Usuarios — Franky Marin (@Franky0010)

Todas estas rutas requieren Administrador; otros roles reciben 403.

| Método/ruta                                 | Entrada y resultado                                                                                                                                                                                                                                                                                                                            |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GET `/usuarios?search=&page=1&page_size=20` | Lista paginada de Usuario. Búsqueda por nombre o email.                                                                                                                                                                                                                                                                                        |
| GET `/usuarios/{id}`                        | 200 Usuario; permite abrir una edición desde un enlace directo                                                                                                                                                                                                                                                                                 |
| POST `/usuarios`                            | `{ "nombre": "Ana", "email": "ana@finca.co", "password": "...", "rol": "operario" }` → 201 Usuario activo                                                                                                                                                                                                                                      |
| PATCH `/usuarios/{id}`                      | Campos editables: `nombre`, `email`, `rol`, `activo`, más `motivo` (texto, máx. 500). **`motivo` es obligatorio si el cambio incluye `activo`** (desactivar o reactivar); sin motivo → 422 `VALIDACION` con `fields.motivo`, sin escribir nada. `motivo` no es un campo del usuario: solo se guarda en la auditoría. → 200 Usuario actualizado |

Correo normalizado trim + minúsculas, único incluso para cuentas inactivas. Nombre requerido (máx. 120), email máx. 254, contraseña propuesta 8..128 caracteres sin recortar espacios (política pendiente de aprobación). Rol de la lista permitida. La UI no ofrece cambiar contraseña en esta fase; no enviar un campo vacío para simularlo. Desactivar es lógico, revoca sesiones y conserva autoría histórica. La UI permite desactivación con confirmación (y debe pedir el motivo) y no ofrece reactivar cuentas todavía, aunque la API ya lo admite con motivo.

Ejemplo de desactivación: `PATCH /usuarios/2` con `{ "activo": false, "motivo": "Renunció" }`.

## Auditoría — base compartida (HT-02)

Solo lectura y solo Administrador; otros roles reciben 403.

| Método/ruta                                                                   | Entrada y resultado                                                                |
| ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| GET `/auditoria?entidad=&entidad_id=&accion=&usuario_id=&page=1&page_size=20` | Lista paginada, del más reciente al más antiguo. Todos los filtros son opcionales. |

Registro público:

```json
{
  "id": 7,
  "entidad": "animal",
  "entidad_id": 25,
  "accion": "cambiar_estado",
  "usuario": "admin@finca.co",
  "usuario_id": 1,
  "momento": "2026-11-04T15:30:00.123456Z",
  "antes": { "estado": "en_produccion", "version": 1 },
  "despues": { "estado": "seco", "fecha_desde": "2026-11-02", "version": 2 },
  "motivo": "Fin del período productivo"
}
```

Reglas:

- La API no ofrece POST, PUT, PATCH ni DELETE sobre `/auditoria` (405). Además, triggers de la base de datos abortan cualquier UPDATE o DELETE sobre la tabla.
- El usuario, el responsable y el momento los fija el servidor a partir de la sesión; la UI nunca los envía.
- No se registran contraseñas, hashes, cookies ni tokens. El servidor rechaza esos nombres de campo en `antes` y `despues`.
- `motivo` es obligatorio en las acciones `corregir`, `anular`, `reactivar`, `desactivar` y `cambiar_estado`.
- `antes` es null en las creaciones. `momento` es un instante UTC ISO 8601.
- Entidades y acciones auditadas hoy: `usuario` (`crear`, `actualizar`, `desactivar`, `reactivar`), `animal` (`crear`, `cambiar_estado`) y `ordeno` (`crear`).

## Animales y estados — Juan Manuel Alvarez (@juanalvarez6)

| Método/ruta                                         | Acceso        | Entrada y resultado                                                                                                                                                                                                 |
| --------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GET `/animales?search=&estado=&page=1&page_size=20` | Tres roles    | **Pendiente (PB-04).** Lista paginada de Animal. Buscar por arete/nombre y filtrar por estado vigente.                                                                                                              |
| GET `/animales/{id}`                                | Tres roles    | 200 Animal con estado vigente y versión; soporte mínimo al formulario de estados                                                                                                                                    |
| POST `/animales`                                    | Administrador | AnimalNuevo → 201 Animal. En una sola transacción crea el animal, su estado inicial (con `fecha_desde` igual a `fecha_ingreso` y motivo automático «Estado inicial al registrar el animal») y la auditoría `crear`. |
| POST `/animales/{id}/estados`                       | Administrador | CambioEstado → 201 `{ "estado": Estado, "animal": Animal }`                                                                                                                                                         |

AnimalNuevo:

```json
{
  "arete": "V-025",
  "nombre": "Luna",
  "raza": "Holstein",
  "procedencia": "Compra",
  "fecha_ingreso": "2026-11-02",
  "fecha_nacimiento": "2022-03-15",
  "edad_estimada_meses": null,
  "estado_inicial": "en_produccion"
}
```

Enviar **exactamente uno** de nacimiento o edad estimada en meses (entero >=0, edad al ingreso); el otro es null. `nombre` opcional/null; arete (máx. 40), raza (máx. 80), procedencia (máx. 160), ingreso y estado inicial requeridos. Rechazar fechas futuras y nacimiento posterior al ingreso. Normalizar arete trim + mayúsculas (no distingue mayúsculas) y no reutilizarlo: el arete es único para siempre porque los animales nunca se borran. El estado inicial permitido en esta UI es en_produccion/seco/no_productivo: un alta fuera del hato requiere el flujo de salida PB-06, fuera de este sprint. Esta restricción de altas es una propuesta a confirmar por el Product Owner. Un `estado_inicial` no permitido responde 422 en el campo `estado_inicial`.

Restricciones también aplicadas en la base de datos: arete único, edad estimada >= 0, nacimiento y edad estimada nunca juntos, nacimiento no posterior al ingreso. Los animales creados por el PoC conservan sus campos nuevos en null.

Animal público: los campos anteriores excepto `estado_inicial`, más `id`, `estado_actual`, `estado_desde`, `version`. `estado_actual` se calcula para la fecha de negocio de hoy; un cambio retroactivo no implica necesariamente cambiar el estado actual si existe otro posterior.

CambioEstado:

```json
{
  "estado": "seco",
  "fecha_desde": "2026-11-02",
  "motivo": "Fin del período productivo",
  "version": 1
}
```

Estado público: `{ "id": 12, "animal_id": 25, "estado": "seco", "fecha_desde": "2026-11-02", "motivo": "...", "responsable_id": 1 }`.

Motivo obligatorio (máx. 500); fecha desde ingreso hasta hoy. Un cambio por animal y día, incluido el estado inicial. Rechazar animales ya retirados, estados iguales al vigente en esa fecha, conflictos con ordeños vigentes y escrituras con versión obsoleta. Comparación/actualización de `version`, inserción del estado y auditoría en una sola transacción; incrementar versión en cada cambio. `fuera_del_hato` se muestra como estado existente, pero la UI de este sprint no permite seleccionarlo: PB-06 requiere tipo de salida y reglas adicionales. La API rechaza `fuera_del_hato` como destino con 422 en el campo `estado`.

Respuestas de `POST /animales/{id}/estados`:

| Caso                                                                                             | Respuesta                             |
| ------------------------------------------------------------------------------------------------ | ------------------------------------- |
| Animal inexistente                                                                               | 404 `NO_ENCONTRADO`                   |
| Estado no permitido, fecha anterior al ingreso o futura, motivo vacío o de más de 500 caracteres | 422 `VALIDACION`, por campo           |
| Estado igual al vigente en esa fecha                                                             | 422 `VALIDACION` en el campo `estado` |
| `version` distinta de la actual (o cambiada por otra persona durante la petición)                | 409 `VERSION_OBSOLETA`                |
| Ya existe un cambio de estado ese día, incluido el inicial                                       | 409 `CAMBIO_DIARIO_DUPLICADO`         |
| Animal ya retirado (`fuera_del_hato`)                                                            | 409 `ESTADO_INCOMPATIBLE`             |
| Pasar a `seco` o `no_productivo` con ordeños **vigentes** (no anulados) desde esa fecha          | 409 `ESTADO_INCOMPATIBLE`             |

La comparación de `version` y su incremento se hacen en una sola sentencia (`UPDATE ... WHERE version = :version`). Si la auditoría o cualquier paso falla antes del commit, la versión, el estado y la auditoría quedan sin cambios.

La ficha/historial completo PB-05 y los ordeños no se implementan aquí. GET animales es soporte mínimo para seleccionar un animal y cambiar su estado. La validación de incompatibilidad debe probarse con datos de ordeño reales o fixtures de backend; el simulador visual no la acredita.

## Errores compartidos

```json
{
  "error": {
    "code": "ARETE_DUPLICADO",
    "message": "Ya existe un animal con ese arete.",
    "fields": { "arete": "Usa un identificador diferente." }
  }
}
```

| HTTP | Códigos y uso                                                                                                                                                      |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 401  | CREDENCIALES_INVALIDAS / SESION_EXPIRADA                                                                                                                           |
| 403  | CUENTA_INACTIVA / SIN_PERMISO / CSRF_INVALIDO                                                                                                                      |
| 404  | NO_ENCONTRADO (entidad); una ruta aún no implementada no se presenta como guardado exitoso                                                                         |
| 405  | METODO_NO_PERMITIDO                                                                                                                                                |
| 409  | EMAIL_DUPLICADO, ARETE_DUPLICADO, CAMBIO_DIARIO_DUPLICADO, ESTADO_INCOMPATIBLE, VERSION_OBSOLETA. Red de seguridad de la base de datos: DUPLICADO, CONFLICTO_DATOS |
| 422  | VALIDACION: mensajes por campo; incluir referencias al campo real del formulario. Red de seguridad: REFERENCIA_INVALIDA (clave foránea inexistente)                |
| 429  | LIMITE_SOLICITUDES, con Retry-After; no repetir automáticamente credenciales                                                                                       |
| 503  | SERVICIO_NO_DISPONIBLE; no afirmar que una escritura se guardó                                                                                                     |

Implementar handlers de FastAPI para normalizar errores de Pydantic y HTTPException. Como transición, el frontend admite `detail` de FastAPI, pero el esquema acordado es `error`. Nunca incluir stack traces ni SQL en respuestas al navegador.

## Respaldo y restauración (RNF06)

- `python -m app.respaldo crear [--carpeta respaldos] [--conservar 14]` genera una copia consistente de la base (API de backup de SQLite), verifica su integridad y conserva las últimas 14.
- `python -m app.respaldo restaurar <archivo>` valida el respaldo, guarda la base actual como `poc.db.previo` y restaura. Detener el servidor antes de restaurar.
- Programar `crear` una vez al día en el sistema operativo (cron o Programador de tareas). Objetivo: pérdida máxima de 24 horas y restauración en menos de 30 minutos. Los respaldos no se versionan en git.
- Cambios de esquema en tablas existentes: `create_all` no los aplica. Mientras no haya migraciones (Alembic, a proponer en el Sprint 2), hay que recrear la base de desarrollo o aplicar `ALTER TABLE`.

## Orden de implementación y comprobación

1. Franky y Juan Manuel revisan este documento. Franky implementa CSRF/sesión/login/logout; Juan Manuel prepara los esquemas y la base compartida de auditoría.
2. Franky implementa usuarios, su auditoría y middleware/dependencias de permisos; Juan Manuel implementa listado, registro y estados versionados de animales.
3. Pruebas de autorización en cada endpoint, CSRF inválido, cuentas inactivas, expiración, duplicados concurrentes, rollback y conflictos de estado.
4. Frontend ejecuta `npm run dev` (API real) y verifica los cinco flujos. `npm run demo` solo usa datos sintéticos en memoria y no hace llamadas al backend.
5. Revisar los criterios originales antes de cerrar cada historia. Aclarar las dependencias PB-01/PB-03 → PB-12 del backlog; esta propuesta no las corrige silenciosamente.

Las pruebas del navegador con respuestas simuladas verifican el cliente, no prueban el servidor. Consultar `frontend/README.md` para reproducirlas y `frontend/src/api.js` para el adaptador que consume este contrato.
