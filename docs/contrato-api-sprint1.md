# Propuesta de contrato API — Sprint 1

**Estado: propuesta para revisión del equipo, no implementada por el PoC.**
Frontend: Juanloaiza25. Backend de acceso/usuarios: compañero 1. Backend de ganado/auditoría: compañero 2. Vinculado a PB-01, PB-02, PB-03, PB-04, PB-11, HT-01 y HT-02.

## Decisiones comunes

- Base `/api/v1`. JSON UTF-8; nombres de campos en español. Identificadores enteros positivos.
- La UI y la API comparten origen. Vite redirige `/api` al FastAPI local en desarrollo. Producción: HTTPS obligatorio.
- El PoC conserva `POST /animales` y `POST /ordenos`. **No conectar los formularios nuevos al `/animales` antiguo:** acepta datos insuficientes. Crear rutas versionadas completas.
- Fechas de negocio `YYYY-MM-DD`, zona America/Bogota, sin convertirlas a UTC. Auditoría: instantes ISO 8601 UTC.
- Listas: `{ "items": [...], "total": 42, "page": 1, "page_size": 20 }`. Parámetros `page` (>=1), `page_size` (1..100), `search` (texto opcional). Orden estable por ID ascendente. Filtrar antes de paginar.
- Roles exactos: `administrador`, `operario`, `propietario`. Estados: `en_produccion`, `seco`, `no_productivo`, `fuera_del_hato`.
- El servidor valida todos los datos y permisos. No aceptar usuario/responsable/fecha de auditoría enviados por la UI. No borrar datos históricos.
- No hay reintentos automáticos de escrituras. Ante pérdida de respuesta, consultar antes de repetir. La unicidad debe ser transaccional.

## Sesión y CSRF — compañero 1

Cookie de sesión opaca `sesion`, HttpOnly, Secure en HTTPS, SameSite=Lax, Path=/. No devolver el token de sesión en JSON ni almacenarlo en localStorage. Timeout de 30 minutos de inactividad en servidor; invalidar al cerrar sesión o desactivar usuario. Verificar rol y estado vigente en cada petición. Respuestas de sesión y CSRF con `Cache-Control: no-store`.

| Método/ruta | Entrada | Respuesta |
|---|---|---|
| GET `/auth/csrf` | Ninguna | 200 `{ "csrf_token": "token-opaco" }`; establecer cookie anónima ligada al token cuando no exista sesión |
| GET `/auth/session` | Cookie | 200 `{ "usuario": Usuario }`; 401 si no hay sesión válida |
| POST `/auth/login` | `{ "email": "admin@finca.co", "password": "..." }` + `X-CSRF-Token` | 200 `{ "usuario": Usuario, "csrf_token": "nuevo-token" }`; rotar ID de sesión y CSRF |
| POST `/auth/logout` | Cookie + `X-CSRF-Token`, sin cuerpo | 204; revocar sesión y borrar cookie |

Todas las escrituras, incluido login/logout, verifican origen y CSRF antes de escribir. GET CSRF entrega un token ligado a la sesión actual, no rota la sesión ni prolonga artificialmente su vigencia. El frontend solicita CSRF antes de cada escritura; no hace polling para mantener la sesión viva.

Usuario público: `{ "id": 1, "nombre": "Ana Pérez", "email": "ana@finca.co", "rol": "administrador", "activo": true }`.

Error de login incorrecto: 401 `CREDENCIALES_INVALIDAS`. Cuenta inactiva: 403 `CUENTA_INACTIVA` **solo después de verificar contraseña**; no revelar si existe una cuenta mediante una contraseña incorrecta. Sesión caducada/revocada: 401 `SESION_EXPIRADA`. El cliente limpia datos de pantallas privadas y vuelve al acceso. Prohibido registrar contraseñas, cookies o tokens en logs.

## Usuarios — compañero 1

Todas estas rutas requieren Administrador; otros roles reciben 403.

| Método/ruta | Entrada y resultado |
|---|---|
| GET `/usuarios?search=&page=1&page_size=20` | Lista paginada de Usuario. Búsqueda por nombre o email. |
| GET `/usuarios/{id}` | 200 Usuario; permite abrir una edición desde un enlace directo |
| POST `/usuarios` | `{ "nombre": "Ana", "email": "ana@finca.co", "password": "...", "rol": "operario" }` → 201 Usuario activo |
| PATCH `/usuarios/{id}` | Campos editables: `nombre`, `email`, `rol`, `activo`. → 200 Usuario actualizado |

Correo normalizado trim + minúsculas, único incluso para cuentas inactivas. Nombre requerido (máx. 120), email máx. 254, contraseña propuesta 8..128 caracteres sin recortar espacios (política pendiente de aprobación). Rol de la lista permitida. La UI no ofrece cambiar contraseña en esta fase; no enviar un campo vacío para simularlo. Desactivar es lógico, revoca sesiones y conserva autoría histórica. La UI permite desactivación con confirmación y no ofrece reactivar cuentas todavía.

## Animales y estados — compañero 2

| Método/ruta | Acceso | Entrada y resultado |
|---|---|---|
| GET `/animales?search=&estado=&page=1&page_size=20` | Tres roles | Lista paginada de Animal. Buscar por arete/nombre y filtrar por estado vigente. |
| GET `/animales/{id}` | Tres roles | 200 Animal con estado vigente y versión; soporte mínimo al formulario de estados |
| POST `/animales` | Administrador | AnimalNuevo → 201 Animal |
| POST `/animales/{id}/estados` | Administrador | CambioEstado → 201 `{ "estado": Estado, "animal": Animal }` |

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

Enviar **exactamente uno** de nacimiento o edad estimada en meses (entero >=0, edad al ingreso); el otro es null. `nombre` opcional/null; arete (máx. 40), raza (máx. 80), procedencia (máx. 160), ingreso y estado inicial requeridos. Rechazar fechas futuras y nacimiento posterior al ingreso. Normalizar arete trim + mayúsculas y no reutilizarlo. El estado inicial permitido en esta UI es en_produccion/seco/no_productivo: un alta fuera del hato requiere el flujo de salida PB-06, fuera de este sprint. Esta restricción de altas es una propuesta a confirmar por el Product Owner.

Animal público: los campos anteriores excepto `estado_inicial`, más `id`, `estado_actual`, `estado_desde`, `version`. `estado_actual` se calcula para la fecha de negocio de hoy; un cambio retroactivo no implica necesariamente cambiar el estado actual si existe otro posterior.

CambioEstado:

```json
{ "estado": "seco", "fecha_desde": "2026-11-02", "motivo": "Fin del período productivo", "version": 1 }
```

Estado público: `{ "id": 12, "animal_id": 25, "estado": "seco", "fecha_desde": "2026-11-02", "motivo": "...", "responsable_id": 1 }`.

Motivo obligatorio (máx. 500); fecha desde ingreso hasta hoy. Un cambio por animal y día, incluido el estado inicial. Rechazar animales ya retirados, estados iguales al vigente en esa fecha, conflictos con ordeños vigentes y escrituras con versión obsoleta. Comparación/actualización de `version`, inserción del estado y auditoría en una sola transacción; incrementar versión en cada cambio. `fuera_del_hato` se muestra como estado existente, pero la UI de este sprint no permite seleccionarlo: PB-06 requiere tipo de salida y reglas adicionales.

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

| HTTP | Códigos y uso |
|---|---|
| 401 | CREDENCIALES_INVALIDAS / SESION_EXPIRADA |
| 403 | CUENTA_INACTIVA / SIN_PERMISO / CSRF_INVALIDO |
| 404 | NO_ENCONTRADO (entidad); una ruta aún no implementada no se presenta como guardado exitoso |
| 409 | EMAIL_DUPLICADO, ARETE_DUPLICADO, CAMBIO_DIARIO_DUPLICADO, ESTADO_INCOMPATIBLE, VERSION_OBSOLETA |
| 422 | VALIDACION: mensajes por campo; incluir referencias al campo real del formulario |
| 429 | LIMITE_SOLICITUDES, con Retry-After; no repetir automáticamente credenciales |
| 503 | SERVICIO_NO_DISPONIBLE; no afirmar que una escritura se guardó |

Implementar handlers de FastAPI para normalizar errores de Pydantic y HTTPException. Como transición, el frontend admite `detail` de FastAPI, pero el esquema acordado es `error`. Nunca incluir stack traces ni SQL en respuestas al navegador.

## Orden de implementación y comprobación

1. Ambos backend revisan este documento. Acceso implementa CSRF/sesión/login/logout; ganado acuerda esquemas y auditoría.
2. Acceso implementa usuarios y middleware/dependencias de permisos; ganado implementa listado, registro y estados versionados.
3. Pruebas de autorización en cada endpoint, CSRF inválido, cuentas inactivas, expiración, duplicados concurrentes, rollback y conflictos de estado.
4. Frontend ejecuta `npm run dev` (API real) y verifica los cinco flujos. `npm run demo` solo usa datos sintéticos en memoria y no hace llamadas al backend.
5. Revisar los criterios originales antes de cerrar cada historia. Aclarar las dependencias PB-01/PB-03 → PB-12 del backlog; esta propuesta no las corrige silenciosamente.

Las pruebas del navegador con respuestas simuladas verifican el cliente, no prueban el servidor. Consultar `frontend/README.md` para reproducirlas y `frontend/src/api.js` para el adaptador que consume este contrato.
