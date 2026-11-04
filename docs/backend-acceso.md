# Backend de acceso y usuarios — Sprint 1

Implementa el contrato de `docs/contrato-api-sprint1.md` para: PB-01 (login, logout, expiración),
PB-02 (cuentas), PB-11 (permisos por rol), HT-01 (seguridad de sesión) y HT-02 (integridad y auditoría de usuarios).

## Primer uso
```bash
pip install -r requirements.txt
# Si ya existe un poc.db de antes, bórrelo: el esquema cambió (no hay migraciones todavía).
python -m app.crear_admin --email admin@finca.co --nombre "Administrador"
uvicorn app.main:app --reload
```

## Variables de entorno
| Variable | Para qué | Por defecto |
|---|---|---|
| `POC_SECRET_KEY` | Firma de los tokens CSRF. Obligatoria fuera de desarrollo; nunca en el repositorio. | Aleatoria por arranque |
| `POC_COOKIE_SECURE` | `1` fuerza cookies Secure (útil detrás de un proxy HTTPS). | Secure solo si la petición es HTTPS |
| `POC_ORIGENES_PERMITIDOS` | Orígenes extra aceptados en escrituras, separados por coma. | Solo el propio sitio |
| `POC_DATABASE_URL` | Base de datos. | `sqlite:///poc.db` |

## Decisiones (a confirmar con el Product Owner)
- Contraseñas con **scrypt** (librería estándar, hash adaptativo, sin dependencias nuevas). Política: 8 a 128 caracteres.
- Un correo incorrecto y una contraseña incorrecta dan la misma respuesta (401); `CUENTA_INACTIVA` solo tras acertar la contraseña.
- Límite de 5 intentos fallidos por IP y correo cada 15 minutos (429 con `Retry-After`); en memoria, válido con un solo proceso.
- Se agregó `ULTIMO_ADMINISTRADOR` (409): no se puede desactivar ni degradar al único administrador activo.
- `GET /auth/csrf` no renueva la sesión; `GET /auth/session` y cualquier otra petición autenticada sí.

## Pendiente / fuera de este sprint
- Las rutas del PoC (`POST /animales`, `POST /ordenos`) siguen **sin sesión**. Deben cerrarse o reemplazarse cuando el backend de ganado y el Sprint 2 las migren a `/api/v1`.
- `Auditoria` ganó las columnas `antes`, `motivo` y `usuario_id`: coordinar con quien implemente la auditoría de animales.
- Falta documentar los endpoints en OpenAPI/README y medir cobertura (HT-04, HT-05).
