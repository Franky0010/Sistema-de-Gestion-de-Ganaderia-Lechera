# Sistema de Gestión de Ganadería Lechera

Proyecto académico de **IS873 — Laboratorio de Software**, Universidad Tecnológica de Pereira.

Aplicación web propuesta para centralizar la información de los animales, registrar ordeños y facilitar el seguimiento de la producción de una finca lechera. Busca reemplazar la consolidación manual de cuadernos y hojas de cálculo por registros consistentes, permisos por rol, historial e indicadores verificables.

**Estado actual:** frontend del sprint 1 rediseñado, con acceso y administración de usuarios integrados al backend de Franky. Se comprobaron login/logout, persistencia y expiración de sesión, creación, edición y desactivación de usuarios, correo duplicado y campos obligatorios. El backend de Juan Manuel incorpora animales, estados y auditoría. Esta entrega completa el listado paginado de animales y el motivo de desactivación exigido por la API; ambos flujos se verificaron desde el navegador.

El diseño combina acceso con paisaje y formulario, navegación lateral carbón y tablas compactas. Usa SVG locales de Google Material Symbols. Se revisaron las pantallas en anchos de 320, 390, 768, 1280 y 1440 px. El paisaje es una imagen decorativa generada, con procedencia incluida en sus archivos.

Para probar la interfaz: `cd frontend`, `npm ci`, `npm run demo`; abrir `http://127.0.0.1:5173/ui/`. Ver [guía del frontend](frontend/README.md) y [propuesta de contrato API para el equipo](docs/contrato-api-sprint1.md).

La entrega de Nota 2 incluye el [informe consolidado](docs/sprint-review-1.md) ([PDF](docs/sprint-review-1.pdf)), el [guion de demostración](docs/demo-sprint1.md), el [script reproducible](scripts/demo_sprint1.py) y el [corte del tablero](docs/evidencia/tablero-2026-11-05.csv).

## Índice

- [Documentación](#documentación)
- [Problema y objetivo](#problema-y-objetivo)
- [Alcance del MVP](#alcance-del-mvp)
- [Roles](#roles)
- [Reglas de negocio](#reglas-de-negocio)
- [Arquitectura y tecnologías](#arquitectura-y-tecnologías)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Instalación y ejecución](#instalación-y-ejecución)
- [API disponible](#api-disponible)
- [Pruebas](#pruebas)
- [Plan de trabajo](#plan-de-trabajo)
- [Calidad y criterios de entrega](#calidad-y-criterios-de-entrega)
- [Trabajo en equipo](#trabajo-en-equipo)
- [Autores](#autores)

## Documentación

| Documento | Contenido |
|---|---|
| [Planteamiento y diseño](docs/planteamiento-y-diseno.md) | Problema, objetivos, RF01–RF13, RNF01–RNF10, casos de uso, arquitectura, modelo de datos y mockups. |
| [Product Backlog](docs/product-backlog.md) | 17 historias funcionales y 5 historias técnicas, criterios de aceptación, prioridades, estimaciones, dependencias y propuesta de sprints. |
| [Prueba de concepto](docs/POC.md) | Riesgo técnico evaluado, procedimiento, resultados y limitaciones de concurrencia y atomicidad. |
| [Frontend](frontend/README.md) | Demo, rutas, pruebas y compilación. |
| [Contrato de API](docs/contrato-api-sprint1.md) | Endpoints y responsables de implementación. |
| [Backend de acceso](docs/backend-acceso.md) | Sesiones, usuarios y configuración. |
| [Sistema visual](DESIGN.md) | Diseño aprobado, componentes y adaptación móvil. |

Las versiones Markdown se pueden leer directamente en GitHub e incluyen índices navegables y las imágenes del diseño. Los archivos Word se conservan tal como fueron entregados y están enlazados al inicio de cada documento para su descarga. El planteamiento todavía describe la ejecución del PoC como pendiente; el código y su informe reflejan el avance posterior. Las estimaciones y la distribución de sprints del backlog son propuestas sujetas a refinamiento.

## Problema y objetivo

Los registros dispersos dificultan consultar el historial de cada animal, consolidar producción por período, identificar errores de captura y saber quién modificó un dato. Las necesidades descritas se validarán con usuarios de la finca; no se presentan entrevistas ni pérdidas económicas verificadas como hechos.

El objetivo es desarrollar, probar y desplegar una aplicación que permita registrar, validar y consultar información productiva de una sola finca, con trazabilidad y alertas internas para apoyar la revisión de variaciones.

## Alcance del MVP

El MVP contempla captura manual en línea y dos turnos diarios: mañana y tarde. Todos los requisitos funcionales son **Must**; los requisitos no funcionales también forman parte de la aceptación.

| Requisito | Funcionalidad prevista | Estado actual |
|---|---|---|
| RF01 | Cuentas, acceso con correo y contraseña, cierre y expiración de sesión. | Implementado e integrado con el frontend; revisión del equipo pendiente. |
| RF02 | Registro de animales, identificación única y estados con fecha efectiva. | Registro, listado y cambios de estado integrados; el flujo de salida del hato continúa en PB-06. |
| RF03 | Consulta de ficha e historial del animal. | Pendiente. |
| RF04 | Registro de producción y descarte por animal, fecha y turno. | Parcial: API del PoC sin sesión real ni validación de estado productivo. |
| RF05 | Validación de cantidades, fechas, estados y duplicados concurrentes. | Parcial: cantidades, turno y unicidad implementados; faltan reglas de fecha y estado. |
| RF06 | Totales de producción, descarte y volumen disponible. | Parcial: centilitros y disponibilidad de un registro; faltan acumulados. |
| RF07 | Consultas por animal y período y comparación entre períodos. | Pendiente. |
| RF08 | Promedio diario y cobertura de turnos. | Pendiente. |
| RF09 | Reportes filtrados dentro de la aplicación. | Pendiente. |
| RF10 | Corrección, anulación y reactivación con motivo y control de versión. | Pendiente; el PoC registra auditoría de creación. |
| RF11 | Autorización en el servidor según el rol vigente. | Implementada para sesión y usuarios; aplicada también a animales; extensión a ordeños pendiente. |
| RF12 | Salidas del rebaño conservando el historial. | Pendiente. |
| RF13 | Alertas internas por disminución de producción y umbral configurable. | Pendiente. |

### Ampliaciones y exclusiones

Los filtros combinados por varios animales y estado son **Should**. Exportación PDF/CSV, sanidad, reproducción, alimentación, lotes y recordatorios son posibles ampliaciones **Could**, posteriores a los Must.

Quedan fuera de esta entrega sensores, funcionamiento sin conexión, múltiples fincas, contabilidad, facturación, predicciones y diagnósticos o prescripciones automáticas. El rol Veterinario se contempla para futuras ampliaciones.

## Roles

Estos permisos describen el objetivo del MVP. La API versionada de usuarios exige Administrador; las rutas antiguas del PoC conservan su alcance experimental.

| Rol | Permisos previstos |
|---|---|
| Administrador | Gestionar cuentas, animales, estados y salidas; registrar y corregir ordeños; configurar umbrales y consultar auditoría. |
| Operario | Registrar ordeños y consultar información. |
| Propietario | Consultar información, reportes e indicadores. |

La API debe verificar permisos en cada operación. La sesión se invalidará al cerrar sesión, desactivar la cuenta o superar 30 minutos de inactividad.

## Reglas de negocio

- **Identificación:** arete único normalizado sin espacios extremos y sin distinguir mayúsculas; no se reutiliza al salir un animal del hato.
- **Estados:** en producción, seco, no productivo y fuera del hato. Los cambios conservan fecha efectiva, motivo e historial.
- **Registro:** clave única por animal, fecha y turno, incluidos registros anulados. El responsable se obtendrá de la sesión autenticada en el MVP.
- **Cantidades:** producción y descarte finitos, no negativos y con hasta dos decimales; descarte no supera producción. Se almacenan como centilitros enteros.
- **Disponibilidad:** producción menos descarte. Los acumulados excluyen ordeños anulados.
- **Datos incompletos:** cero litros es válido; un turno ausente no equivale a cero.
- **Promedio diario:** producción del día dividida entre animales distintos con al menos un ordeño vigente; se informa la cobertura de ambos turnos.
- **Comparación:** períodos de igual duración y mismos filtros. Variación = (total actual − total previo) / total previo × 100; con referencia cero se muestra «No calculable».
- **Trazabilidad:** correcciones, anulaciones y reactivaciones exigen motivo y versión; no alteran creador ni fecha original. Datos, auditoría y efectos asociados deben confirmarse o revertirse juntos.
- **Salidas:** venta, muerte, descarte, robo o traslado, registradas en ESTADO_ANIMAL con fecha efectiva y motivo.
- **Tiempo:** fechas de negocio en America/Bogota e instantes de auditoría en UTC, según el diseño del MVP.

### Alertas de producción previstas

RF13 compara la producción diaria, sin restar descarte, con el promedio de los siete días calendario inmediatamente anteriores. Los ocho días deben tener ambos turnos y pertenecer a un intervalo continuo en producción.

Disminución = (promedio previo − producción del día) / promedio previo × 100. El umbral inicial es 20 %; solo el administrador podrá modificarlo, con vigencia desde el día siguiente y conservación de su historial.

Se prevé una alerta por animal y fecha si la disminución alcanza el umbral. Los turnos faltantes se informan como «Datos incompletos»; una referencia cero o cambio de estado, como «No evaluable». Los cambios de ordeños recalculan el día afectado y hasta siete fechas posteriores con el umbral histórico aplicable. Las alertas apoyan la revisión y no constituyen diagnósticos.

## Arquitectura y tecnologías

El diseño propone una aplicación cliente-servidor con API REST y persistencia en el servidor.

| Componente | Tecnología | Situación |
|---|---|---|
| Interfaz | HTML, Tailwind CSS y JavaScript con Vite | Rediseño adaptable; sesión, usuarios, registro y cambios de estado integrados. |
| API | Python y FastAPI | Sesión y usuarios en /api/v1, más rutas del PoC. |
| Validación | Pydantic y servicios de negocio | Implementación parcial. |
| Persistencia | SQLAlchemy y SQLite | Usuarios, sesiones, auditoría y datos del PoC. |
| Servidor local | Uvicorn | Disponible mediante las dependencias. |
| Pruebas | pytest, httpx, Node y Playwright | Backend, validaciones del cliente y flujos de navegador. |

La arquitectura objetivo separa rutas y esquemas, servicios de negocio y repositorios. Actualmente los servicios acceden a SQLAlchemy directamente; la capa de repositorios es trabajo pendiente.

El modelo completo contempla usuarios, animales, estados, ordeños, auditoría e información para alertas y umbrales. El código actual define Usuario, Sesion, Animal, Ordeno y Auditoria.

SQLite utiliza claves foráneas, WAL y espera acotada ante bloqueos. PostgreSQL se evaluará si las pruebas de carga evidencian limitaciones. El despliegue del MVP deberá incorporar HTTPS, secretos fuera del repositorio, almacenamiento persistente y respaldo/restauración documentados.

## Estructura del repositorio

```text
.
├── app/
│   ├── __init__.py
│   ├── database.py       # SQLite, PRAGMA y sesiones
│   ├── main.py           # API versionada y rutas del PoC
│   ├── rutas_auth.py     # Login, logout, CSRF y sesión
│   ├── rutas_usuarios.py # Administración de cuentas
│   ├── seguridad.py     # Contraseñas, CSRF y límites de acceso
│   ├── models.py         # Usuarios, sesiones, animales, ordeños y auditoría
│   └── service.py        # Validaciones y transacción de ordeño/auditoría
├── frontend/            # Vite, HTML, Tailwind CSS y JavaScript
│   ├── src/views.js     # Pantallas y formularios
│   ├── src/styles.css   # Diseño adaptable
│   ├── src/api.js       # Cliente de /api/v1
│   ├── src/assets/      # Paisaje e iconos locales
│   └── tests/           # Pruebas unitarias y de navegador
├── docs/
│   ├── contrato-api-sprint1.md
│   ├── backend-acceso.md
│   ├── assets/planteamiento-y-diseno/  # Diagramas y mockups
│   ├── POC.md
│   ├── planteamiento-y-diseno.md
│   ├── planteamiento-y-diseno.docx
│   ├── product-backlog.md
│   └── product-backlog.docx
├── tests/
│   ├── __init__.py
│   ├── test_poc.py
│   ├── test_auth.py
│   ├── test_seguridad.py
│   └── test_usuarios.py
├── .gitignore
├── pytest.ini
├── requirements.txt     # Dependencias fijadas
└── README.md
```

## Instalación y ejecución

Estas instrucciones permiten ejecutar el frontend con la API y una base SQLite local.

### Requisitos

- Git.
- Python 3.11 o posterior; la integración se verificó en Windows con Python 3.11.
- Node.js 22.12 o posterior y npm.
- Acceso a Internet para instalar dependencias.

```bash
git clone https://github.com/Franky0010/Sistema-de-Gestion-de-Ganaderia-Lechera.git
cd Sistema-de-Gestion-de-Ganaderia-Lechera
python -m venv .venv
```

Windows PowerShell, sin necesidad de activar scripts:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:POC_DATABASE_URL = 'sqlite:///login-pruebas.db'
$env:POC_ORIGENES_PERMITIDOS = 'http://localhost:5187,http://127.0.0.1:5187,http://localhost:5173,http://127.0.0.1:5173'
.\.venv\Scripts\python.exe -m app.crear_admin --email admin@finca.co --nombre 'Admin de prueba'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Linux o macOS:

```bash
.venv/bin/python -m pip install -r requirements.txt
export POC_DATABASE_URL=sqlite:///login-pruebas.db
export POC_ORIGENES_PERMITIDOS=http://localhost:5187,http://127.0.0.1:5187,http://localhost:5173,http://127.0.0.1:5173
.venv/bin/python -m app.crear_admin --email admin@finca.co --nombre 'Admin de prueba'
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

La contraseña se solicita por consola (8 a 128 caracteres). Crear el administrador es un paso inicial; en arranques posteriores se reutiliza la cuenta. El entorno virtual dentro del repositorio evita la redirección de AppData de Python de Microsoft Store.

En otra terminal, desde la raíz del repositorio:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev -- --host localhost --port 5187
```

En Linux/macOS usar `npm` en lugar de `npm.cmd`. Abrir [el frontend](http://localhost:5187/ui/) y entrar con la cuenta creada. Vite redirige `/api` a `http://127.0.0.1:8000`.

Si el login devuelve `403` con «Origen de la solicitud no permitido», comprobar que la dirección del navegador (protocolo, host y puerto) esté en `POC_ORIGENES_PERMITIDOS`. La configuración local anterior admite `localhost` y `127.0.0.1` en los puertos 5173 y 5187. Después de cambiarla, reiniciar Uvicorn desde esa misma terminal y recargar el frontend. No desactivar la validación CSRF. Un `401` de `/auth/session` antes de iniciar sesión es normal. En despliegues, configurar únicamente los orígenes reales autorizados.

Después del acceso se abre Animales con búsqueda y filtro de estado. Usuarios permite crear, editar y desactivar cuentas; la desactivación solicita un motivo para la auditoría.

También están disponibles [Swagger UI](http://127.0.0.1:8000/docs) y [OpenAPI JSON](http://127.0.0.1:8000/openapi.json).

### Base de datos

Al iniciar la API se crean las tablas si no existen. Por defecto usa `poc.db` en el directorio de ejecución. Configurar `POC_DATABASE_URL` antes de arrancar permite elegir otro archivo SQLite:

```powershell
$env:POC_DATABASE_URL = "sqlite:///poc-local.db"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

```bash
POC_DATABASE_URL=sqlite:///poc-local.db .venv/bin/python -m uvicorn app.main:app --reload
```

Los comandos de inicio anteriores utilizan `login-pruebas.db`, conservando las cuentas entre arranques. Cada integrante tiene su propia base local. Para ensayar un esquema nuevo, elegir un archivo nuevo y conservar el anterior; aún no hay migraciones automáticas. Git ignora las bases locales, los entornos virtuales y cualquier carpeta `.impeccable/`.

La configuración es específica de SQLite; cambiar la URL no implementa por sí solo compatibilidad con PostgreSQL.

## API disponible

| Método | Ruta | Uso |
|---|---|---|
| GET | /api/v1/auth/csrf | Obtener token CSRF para escrituras. |
| GET | /api/v1/auth/session | Consultar el usuario de la sesión vigente. |
| POST | /api/v1/auth/login | Iniciar sesión mediante cookie. |
| POST | /api/v1/auth/logout | Revocar sesión y borrar cookie. |
| GET | /api/v1/usuarios | Lista paginada y búsqueda (Administrador). |
| GET | /api/v1/usuarios/{id} | Consultar una cuenta (Administrador). |
| POST | /api/v1/usuarios | Crear una cuenta (Administrador). |
| PATCH | /api/v1/usuarios/{id} | Editar datos, rol o estado activo (Administrador). |
| GET | /api/v1/animales | Lista paginada con búsqueda y estado efectivo. |
| POST | /api/v1/animales | Registro completo (Administrador). |
| GET | /api/v1/animales/{id} | Consultar animal. |
| GET | /api/v1/animales/{id}/estados | Historial paginado. |
| POST | /api/v1/animales/{id}/estados | Cambiar estado con fecha, motivo y versión (Administrador). |
| GET | /api/v1/auditoria | Consultar auditoría (Administrador). |
| POST | /animales | Crear un animal con arete y nombre opcional. |
| POST | /ordenos | Registrar un ordeño y su auditoría. |
| GET | /docs | Documentación interactiva. |
| GET | /openapi.json | Esquema OpenAPI. |

Las escrituras versionadas requieren `X-CSRF-Token`; el frontend lo obtiene antes de cada envío. El [contrato](docs/contrato-api-sprint1.md) detalla entradas, respuestas y errores.

Para probar las rutas antiguas del PoC en Swagger UI, ejecutar primero `POST /animales`:

```json
{"arete": "V-001", "nombre": "Luna"}
```

Copiar el `id` devuelto y usarlo en `POST /ordenos`, con la cabecera `X-Usuario: operario01`:

```json
{
  "animal_id": 1,
  "fecha": "2026-10-06",
  "turno": "mañana",
  "litros_producidos": "12.50",
  "litros_descartados": "0.50",
  "observaciones": "Registro de demostración"
}
```

La respuesta válida es `201`, con producción, descarte y disponibilidad. Repetir la combinación de animal, fecha y turno devuelve `409`.

**X-Usuario es un sustituto de sesión para el PoC, controlado por el cliente.** No demuestra autenticación ni autorización y debe reemplazarse por identidad autenticada en el MVP.

| Código | Significado |
|---|---|
| 201 | Registro creado. |
| 404 | Animal inexistente al registrar un ordeño. |
| 409 | Arete o clave de ordeño duplicados. |
| 422 | Entrada inválida, cantidad fuera de rango o cabecera requerida ausente. |
| 503 | Bloqueo de SQLite que persiste tras la espera acotada al registrar ordeños. |

## Pruebas

El rediseño pasó 6 pruebas unitarias del cliente y 7 pruebas Playwright. Se comprobaron además los flujos de sesión y usuarios contra el backend real con una base temporal, incluidos campos obligatorios, correo duplicado, desactivación y expiración. La revisión visual cubrió cinco anchos entre 320 y 1440 px.

Desde `frontend/`:

```powershell
npm.cmd test
npm.cmd run test:e2e
npm.cmd run build
```

Playwright usa Chrome o Edge instalados en Windows y levanta servidores en 5173/5174. En otros entornos instalar Chromium con `npx playwright install chromium`. La suite del navegador usa demo y respuestas interceptadas; la comprobación integrada con el backend real se realizó por separado.

Desde la raíz del repositorio, en Windows:

```powershell
.\.venv\Scripts\python.exe -m pytest -v -s
```

En Linux o macOS:

```bash
.venv/bin/python -m pytest -v -s
```

La suite utiliza archivos SQLite temporales y cubre:

- Registro válido, cero litros y conversión a centilitros.
- Dos solicitudes concurrentes con la misma clave, repetidas 50 veces.
- Ocho hilos compitiendo por una única clave.
- Reversión completa ante un fallo antes del commit.
- Cantidades inválidas y animal inexistente.
- Aretes vacíos, normalización y unicidad.
- Cantidades extremas y persistencia exacta del límite entero de SQLite.

La revisión integrada mediante el PR #1 obtuvo **23 pruebas aprobadas**. Verifican el escenario acotado del PoC; no acreditan todavía rendimiento, seguridad, usabilidad ni el MVP completo. El procedimiento y los resultados originales se conservan en [docs/POC.md](docs/POC.md).

## Plan de trabajo

El backlog agrupa 22 elementos en seis épicas: acceso y usuarios, gestión del ganado, producción de leche, reportes e indicadores, alertas y calidad técnica.

| Sprint propuesto | Objetivo |
|---|---|
| 1 | Acceso, usuarios, animales y base de seguridad e integridad. |
| 2 | Ordeños, estados/salidas, correcciones e historial. |
| 3 | Consultas, comparaciones, indicadores, reportes y alertas. |
| 4 | Integración, rendimiento, validación y despliegue. |

Se proponen ciclos de dos semanas, sujetos al calendario académico y la capacidad real del equipo. Los puntos de historia son estimaciones iniciales, no horas ni compromisos confirmados. Seguridad y pruebas se trabajan desde el inicio.

## Calidad y criterios de entrega

Los RNF01–RNF10 establecen seguridad, disponibilidad de ensayo, usabilidad, rendimiento, evolución de persistencia, integridad, auditoría, mantenibilidad, portabilidad y pruebas.

Entre las metas previstas están:

- Hash adaptativo de contraseñas, HTTPS, cookies de sesión protegidas y protección CSRF.
- Al menos 99 % de respuestas exitosas en una ventana de evaluación acordada de ocho horas; no equivale a un SLA de producción.
- Guardado de ordeños y listado de animales por debajo de 2 s en P95; reportes de hasta 90 días por debajo de 3 s, excluyendo latencia de Internet.
- Interfaz adaptable a computador y móvil, navegación por teclado y compatibilidad con Chrome, Firefox y Edge.
- Evidencia de integridad, concurrencia, permisos y trazabilidad mediante pruebas.

Un elemento está terminado cuando cumple sus criterios de aceptación, tiene pruebas aprobadas, revisión de código, documentación actualizada y demostración integrada. El MVP requiere todos los Must, validación de los RNF y ausencia de defectos críticos abiertos.

## Trabajo en equipo

1. Relacionar cada cambio con el requisito y elemento del backlog correspondiente.
2. Trabajar en una rama y abrir un pull request con el problema, la solución y la validación.
3. Ejecutar las pruebas afectadas y mantener las dependencias fijadas.
4. Actualizar este README cuando cambie el estado real de implementación.
5. Sincronizar diseño y backlog al aprobar cambios de alcance.

## Autores

- Juan Manuel Alvarez
- Franky Marin
- Juan Diego Niño

Universidad Tecnológica de Pereira · Pereira, Risaralda · 2026.
