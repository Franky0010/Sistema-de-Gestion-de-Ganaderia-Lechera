# Sistema de Gestión de Ganadería Lechera

Proyecto académico de **IS873 — Laboratorio de Software**, Universidad Tecnológica de Pereira.

Aplicación web propuesta para centralizar la información de los animales, registrar ordeños y facilitar el seguimiento de la producción de una finca lechera. Busca reemplazar la consolidación manual de cuadernos y hojas de cálculo por registros consistentes, permisos por rol, historial e indicadores verificables.

**Estado actual:** el repositorio contiene una prueba de concepto ejecutable de registro de ordeños con control de duplicados, validación de cantidades y auditoría transaccional. La interfaz web, autenticación y demás módulos del MVP están planificados; todavía no están implementados.

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
| [Planteamiento y diseño (.docx)](docs/planteamiento-y-diseno.docx) | Problema, objetivos, RF01–RF13, RNF01–RNF10, casos de uso, arquitectura, modelo de datos y mockups. |
| [Product Backlog (.docx)](docs/product-backlog.docx) | 17 historias funcionales y 5 historias técnicas, criterios de aceptación, prioridades, estimaciones, dependencias y propuesta de sprints. |
| [Prueba de concepto](docs/POC.md) | Riesgo técnico evaluado, procedimiento, resultados y limitaciones de concurrencia y atomicidad. |

Los archivos Word se conservan tal como fueron entregados. El planteamiento todavía describe la ejecución del PoC como pendiente; el código y su informe reflejan el avance posterior. Las estimaciones y la distribución de sprints del backlog son propuestas sujetas a refinamiento.

## Problema y objetivo

Los registros dispersos dificultan consultar el historial de cada animal, consolidar producción por período, identificar errores de captura y saber quién modificó un dato. Las necesidades descritas se validarán con usuarios de la finca; no se presentan entrevistas ni pérdidas económicas verificadas como hechos.

El objetivo es desarrollar, probar y desplegar una aplicación que permita registrar, validar y consultar información productiva de una sola finca, con trazabilidad y alertas internas para apoyar la revisión de variaciones.

## Alcance del MVP

El MVP contempla captura manual en línea y dos turnos diarios: mañana y tarde. Todos los requisitos funcionales son **Must**; los requisitos no funcionales también forman parte de la aceptación.

| Requisito | Funcionalidad prevista | Estado actual |
|---|---|---|
| RF01 | Cuentas, acceso con correo y contraseña, cierre y expiración de sesión. | Pendiente. |
| RF02 | Registro de animales, identificación única y estados con fecha efectiva. | Parcial: alta mínima con arete y nombre opcional. |
| RF03 | Consulta de ficha e historial del animal. | Pendiente. |
| RF04 | Registro de producción y descarte por animal, fecha y turno. | Parcial: API del PoC sin sesión real ni validación de estado productivo. |
| RF05 | Validación de cantidades, fechas, estados y duplicados concurrentes. | Parcial: cantidades, turno y unicidad implementados; faltan reglas de fecha y estado. |
| RF06 | Totales de producción, descarte y volumen disponible. | Parcial: centilitros y disponibilidad de un registro; faltan acumulados. |
| RF07 | Consultas por animal y período y comparación entre períodos. | Pendiente. |
| RF08 | Promedio diario y cobertura de turnos. | Pendiente. |
| RF09 | Reportes filtrados dentro de la aplicación. | Pendiente. |
| RF10 | Corrección, anulación y reactivación con motivo y control de versión. | Pendiente; el PoC registra auditoría de creación. |
| RF11 | Autorización en el servidor según el rol vigente. | Pendiente. |
| RF12 | Salidas del rebaño conservando el historial. | Pendiente. |
| RF13 | Alertas internas por disminución de producción y umbral configurable. | Pendiente. |

### Ampliaciones y exclusiones

Los filtros combinados por varios animales y estado son **Should**. Exportación PDF/CSV, sanidad, reproducción, alimentación, lotes y recordatorios son posibles ampliaciones **Could**, posteriores a los Must.

Quedan fuera de esta entrega sensores, funcionamiento sin conexión, múltiples fincas, contabilidad, facturación, predicciones y diagnósticos o prescripciones automáticas. El rol Veterinario se contempla para futuras ampliaciones.

## Roles

Estos permisos son el objetivo del MVP; el PoC aún no los aplica.

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
| Interfaz | HTML, Tailwind CSS y JavaScript | Propuesta; sin frontend implementado. |
| API | Python y FastAPI | Implementada de forma mínima para el PoC. |
| Validación | Pydantic y servicios de negocio | Implementación parcial. |
| Persistencia | SQLAlchemy y SQLite | Implementada en el PoC. |
| Servidor local | Uvicorn | Disponible mediante las dependencias. |
| Pruebas | pytest y httpx | Suite del PoC y regresiones. |

La arquitectura objetivo separa rutas y esquemas, servicios de negocio y repositorios. Actualmente los servicios acceden a SQLAlchemy directamente; la capa de repositorios es trabajo pendiente.

El modelo completo contempla usuarios, animales, estados, ordeños, auditoría e información para alertas y umbrales. El PoC solo define Animal, Ordeno y Auditoria.

SQLite utiliza claves foráneas, WAL y espera acotada ante bloqueos. PostgreSQL se evaluará si las pruebas de carga evidencian limitaciones. El despliegue del MVP deberá incorporar HTTPS, secretos fuera del repositorio, almacenamiento persistente y respaldo/restauración documentados.

## Estructura del repositorio

```text
.
├── app/
│   ├── __init__.py
│   ├── database.py       # SQLite, PRAGMA y sesiones
│   ├── main.py           # API mínima y esquemas de entrada
│   ├── models.py         # Animal, Ordeno y Auditoria
│   └── service.py        # Validaciones y transacción de ordeño/auditoría
├── docs/
│   ├── POC.md
│   ├── planteamiento-y-diseno.docx
│   └── product-backlog.docx
├── tests/
│   ├── __init__.py
│   └── test_poc.py
├── .gitignore
├── pytest.ini
├── requirements.txt     # Dependencias fijadas
└── README.md
```

## Instalación y ejecución

Estas instrucciones ejecutan el backend del PoC. No existe todavía una pantalla de acceso ni interfaz web del MVP.

### Requisitos

- Git.
- Python **3.13** recomendado para reproducir el entorno de pruebas verificado.
- Acceso a Internet para instalar dependencias.

```bash
git clone https://github.com/Franky0010/Sistema-de-Gestion-de-Ganaderia-Lechera.git
cd Sistema-de-Gestion-de-Ganaderia-Lechera
python -m venv .venv
```

Windows PowerShell, sin necesidad de activar scripts:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Linux o macOS:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --reload
```

Abrir [Swagger UI](http://127.0.0.1:8000/docs) o [OpenAPI JSON](http://127.0.0.1:8000/openapi.json). El modo `--reload` es para desarrollo.

### Base de datos

Al iniciar la API se crean las tablas si no existen. Por defecto usa `poc.db` en el directorio de ejecución. Configurar `POC_DATABASE_URL` antes de arrancar permite elegir otro archivo SQLite:

```powershell
$env:POC_DATABASE_URL = "sqlite:///poc-local.db"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

```bash
POC_DATABASE_URL=sqlite:///poc-local.db .venv/bin/python -m uvicorn app.main:app --reload
```

La configuración es específica de SQLite; cambiar la URL no implementa por sí solo compatibilidad con PostgreSQL.

## API disponible

| Método | Ruta | Uso |
|---|---|---|
| POST | /animales | Crear un animal con arete y nombre opcional. |
| POST | /ordenos | Registrar un ordeño y su auditoría. |
| GET | /docs | Documentación interactiva. |
| GET | /openapi.json | Esquema OpenAPI. |

En Swagger UI, ejecutar primero `POST /animales`:

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
