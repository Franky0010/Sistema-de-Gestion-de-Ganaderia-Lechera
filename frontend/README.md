# Frontend del sprint 1

HTML, Tailwind CSS compilado y JavaScript modular. Sin framework adicional. Vite se usa para desarrollo y compilación; Node 22.12+ recomendado.

## Ejecutar la demostración

Desde PowerShell:

```powershell
cd "C:\Users\juand\Documents\LabSoft\Sistema-de-Gestion-de-Ganaderia-Lechera\frontend"
npm ci
npm run demo
```

Abrir `http://127.0.0.1:5173/ui/`. En el acceso, seleccionar Administrador, Operario o Propietario para completar las credenciales; pulsar Iniciar sesión. La contraseña de todas las cuentas de muestra es `Demo12345`.

**Demo aislada:** registros ficticios en memoria, sin llamadas al backend y sin persistencia. Recargar reinicia los cambios y la sesión. No introducir contraseñas ni datos personales reales. La cuenta `inactivo@demo.local` permite probar el error de cuenta inactiva.

## Conectar el backend

```powershell
npm run dev
```

El cliente usa `/api/v1` y Vite redirige `/api` a `http://127.0.0.1:8000`. Sesión y usuarios están implementados e integrados según el [contrato](../docs/contrato-api-sprint1.md). También están disponibles el listado, registro y cambios de estado de animales. La desactivación de usuarios solicita un motivo conforme al contrato. Para crear el administrador y configurar el origen permitido, seguir las [instrucciones del README principal](../README.md#instalación-y-ejecución). El cliente conserva los errores de la API para que puedan corregirse.

### Reparto para integrar

- Franky Marin (@Franky0010): CSRF/sesión/login/logout, listado/detalle/alta/edición de usuarios, autorización por rol.
- Juan Manuel Alvarez (@juanalvarez6): listado/detalle/registro de animales, cambios de estado, versión y auditoría transaccional.
- Juanloaiza25: las cinco pantallas, consumo de API, validaciones visuales, errores, adaptación móvil y pruebas del navegador.

Los permisos en el navegador solo controlan la experiencia. La protección real, expiración, auditoría y reglas de integridad pertenecen al servidor.

## Flujos y rutas del cliente

| Ruta hash | Uso |
|---|---|
| `#/login` | Acceso, errores y credenciales demo solo en modo demo |
| `#/animales` | Lista, búsqueda, filtro de estado y paginación |
| `#/animales/nuevo` | Registro, nacimiento o edad estimada en meses |
| `#/animales/{id}/estado` | Fecha, motivo, estado y control de versión |
| `#/usuarios` | Listado y desactivación con confirmación |
| `#/usuarios/nuevo` | Creación de cuenta con rol |
| `#/usuarios/{id}/editar` | Edición de datos y rol |

Cambiar estado, crear animales y administrar usuarios requiere Administrador. Operario/Propietario tienen consulta del hato. No se muestran botones para módulos futuros que aún no funcionan.

Un error 401 en una operación privada limpia la pantalla y vuelve al login. Los 403 se muestran como falta de permiso; errores por campo conservan los valores para corregirlos. No hay reintentos automáticos de escritura ni autenticación en localStorage.

## Validación

```powershell
npm test
npm run test:e2e
npm run build
```

Playwright usa Chrome o Edge instalados en Windows; en otros entornos instalar Chromium con `npx playwright install chromium`. Los tests levantan una demo en 5173 y la variante API en 5174. Las pruebas API del navegador interceptan respuestas según el contrato: **no son pruebas del backend real**. Las capturas quedan en `.impeccable/review/` en la raíz del repositorio, ignoradas por Git.

El rediseño se comprobó con capturas en 320, 390, 768, 1280 y 1440 px. Se corrigieron el texto del selector de edad en móvil y la distribución de acciones en tablet. Los SVG oficiales de Google Material Symbols se sirven desde los assets locales.

## Producción

`npm run build` genera `dist/` con base `/ui/`. El modo demo no está incluido en esa compilación. Servir `dist` en `/ui/` junto con `/api/v1` bajo el mismo origen HTTPS. Las rutas del cliente usan hash y no requieren reescrituras por ruta.

Una vez implementadas las rutas API, el backend puede añadir, al final de su configuración, un montaje estático (no se modifica el PoC en esta entrega):

```python
from pathlib import Path
from fastapi.staticfiles import StaticFiles

ui = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if ui.exists():
    app.mount("/ui", StaticFiles(directory=ui, html=True), name="ui")
```

HTTPS, cookies seguras, protección CSRF, cabeceras de seguridad y almacenamiento persistente deben configurarse en el servidor. Esta entrega no prepara un despliegue público ni implementa el backend pendiente.

## Límites del avance

Las subtareas #26, #28, #32 y #34 tienen comprobaciones con la API real. El informe de [Sprint Review 1](../docs/sprint-review-1.md) detalla límites, revisión pendiente y diferencias entre el estado del tablero y el cierre completo de las historias.
