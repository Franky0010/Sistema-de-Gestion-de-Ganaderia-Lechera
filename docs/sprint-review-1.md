# Sprint Planning y Sprint Review 1

IS873 - Laboratorio de Software | Nota 2 | Sistema de Gestión de Ganadería Lechera

Corte de revisión: 5 de noviembre de 2026 (America/Bogota). Base revisada: main, commit f2bdcce, con correcciones de integración preparadas en la rama docs/nota2-sprint-review1.

## 1. Planificación y alcance

**Sprint Goal propuesto para ratificación:** permitir al administrador acceder de forma segura, gestionar cuentas y registrar animales con cambios de estado trazables desde una interfaz web.

La planificación se reconstruye a partir del backlog de Nota 1 y las subtareas de GitHub. El equipo confirmó que no registró las fechas del sprint ni la disponibilidad de horas por integrante. No existe una capacidad numérica verificable ni una velocidad histórica con la que justificar la carga. La guía de Nota 2 contempla aproximadamente tres semanas; Nota 1 proponía ciclos de dos semanas. El equipo debe reconocer esta diferencia en la sustentación.

El alcance de referencia coincide con el apartado 5.1 de Nota 1. La siguiente tabla conserva sus prioridades y estimaciones iniciales; no demuestra que se celebrara una reunión de compromiso con esa carga.

| Orden | Historia | Prioridad | Estimación de Nota 1 | Responsable de ejecución |
|---|---|---|---|---|
| 1 | HT-01 Seguridad de autenticación y sesión | Must | 8 SP | Franky; integración frontend de Juan Diego |
| 2 | PB-01 Iniciar y cerrar sesión | Must | 5 SP | Franky y Juan Diego |
| 3 | PB-02 Administrar cuentas de usuario | Must | 5 SP | Franky y Juan Diego |
| 4 | PB-03 Registrar animales | Must | 8 SP | Juan Manuel y Juan Diego |
| 5 | PB-04 Cambiar el estado productivo | Must | 5 SP | Juan Manuel y Juan Diego |
| 6 | PB-11 Aplicar permisos por rol | Must | 5 SP | Franky y Juan Diego; Juan Manuel en animales |
| 7 | HT-02 Integridad y auditoría transaccional (inicio) | Must | 8 SP para la historia completa | Juan Manuel; Franky en usuarios |

Las seis historias completas suman 36 SP iniciales. HT-02 aporta un alcance parcial sin estimación separada: 44 SP es la suma nominal del backlog si se cuenta toda HT-02, no la capacidad ni los puntos terminados del sprint. Las subtareas no agregan puntos a la historia padre.

### Justificación de la selección

| Historia | Valor y dependencias | Capacidad y prioridad relativa |
|---|---|---|
| HT-01 | Protege cuentas y cambios; habilita acceso y permisos. | Trabajo backend de Franky en paralelo con la interfaz. Se prioriza por riesgo de seguridad. Horas no registradas. |
| PB-01 | Permite usar el incremento con identidad; depende de HT-01. | Franky implementa sesión y Juan Diego el acceso; habilita todas las pantallas privadas. |
| PB-02 | Permite distribuir acceso por rol; depende de PB-01 y HT-01. | Se reutiliza la base de seguridad; dos responsables reparten API e interfaz. |
| PB-03 | Crea el registro maestro del ganado; depende de acceso e integridad. | Juan Manuel trabaja en datos y Juan Diego en formularios; antecede a estados y ordeños. |
| PB-04 | Conserva evolución del animal; depende de PB-03 y HT-02. | Reutiliza animal y auditoría; se demuestra una incompatibilidad usando datos del PoC de ordeños. |
| PB-11 | Evita acciones de roles no autorizados; depende de PB-01, PB-02 y HT-01. | Se incorpora en los endpoints del corte. Los permisos de módulos futuros continúan pendientes. |
| HT-02 | Evita escrituras parciales y registra autoría; depende de HT-01. | Se inicia en usuarios, animales y estados; Nota 1 prevé su continuación en sprint 2. |

Estas razones explican prioridad y reparto, pero no sustituyen una planificación de capacidad. Para Nota 3 se debe registrar disponibilidad individual, estimar el alcance parcial y acordar una carga antes de iniciar.

Nota 1 declara PB-12 como dependencia de PB-01 y PB-03, aunque PB-12 corresponde a consultas de producción del sprint 3. La implementación actual no requiere esa consulta para autenticar o registrar animales. Se propone revisar esa dependencia con el docente y dejar el cambio aprobado en el backlog; aquí se conserva la discrepancia.

### Historias fuera de este corte

| Historias | Razón y continuidad |
|---|---|
| PB-05, PB-06 | Ficha completa y salidas requieren consolidar registro, estados y trazabilidad. Propuestas para sprint 2. |
| PB-07, PB-08, PB-09, PB-10 | Ordeños, validación, totales y correcciones requieren animales y permisos integrados. El PoC aporta evidencia parcial, no el alcance completo. Sprint 2. |
| PB-12, PB-13, PB-14, PB-15 | Consultas, comparaciones, indicadores y reportes dependen de producción persistida. Sprint 3. |
| PB-16, PB-17 | Alertas y umbral dependen de series completas de producción. Sprint 3. |
| HT-03 | Hubo trabajo responsive y accesibilidad, pero falta verificar Chrome, Firefox y Edge y los flujos futuros. El backlog sitúa su cierre en sprint 3. |
| HT-04, HT-05 | Rendimiento, disponibilidad, revisión integral y despliegue dependen del MVP completo. Sprint 4, con pruebas iniciadas desde este corte. |

## 2. Criterios de aceptación y Definition of Done

Los criterios siguientes se transcriben de Nota 1. Un criterio que excede el incremento queda identificado en los resultados, aunque exista una subtarea terminada.

### HT-01 — Implementar seguridad de autenticación y sesión

1. Las contraseñas usan hash adaptativo y los secretos permanecen fuera del repositorio.

2. El despliegue utiliza HTTPS y cookies HttpOnly, Secure y SameSite.

3. Las operaciones de cambio incluyen protección CSRF y la API valida usuario activo y permisos.

### PB-01 — Iniciar y cerrar sesión

1. El sistema acepta credenciales válidas de una cuenta activa y rechaza credenciales inválidas o cuentas inactivas.

2. La sesión expira después de 30 minutos de inactividad y las solicitudes posteriores son rechazadas.

3. Al cerrar sesión se invalida la sesión vigente y no se exponen credenciales en la interfaz ni en los registros.

### PB-02 — Administrar cuentas de usuario

1. El correo electrónico es único y se validan nombre, contraseña y rol.

2. Una cuenta desactivada no puede iniciar sesión y sus registros históricos se conservan.

3. Operarios y propietarios no pueden administrar cuentas.

### PB-03 — Registrar animales

1. Se exige arete, raza, procedencia, fecha de ingreso, nacimiento o edad estimada y estado inicial; el nombre es opcional.

2. El arete se normaliza sin espacios extremos, no distingue mayúsculas y no puede repetirse ni reutilizarse.

3. Se rechazan fechas futuras o un nacimiento posterior al ingreso y la creación queda auditada.

### PB-04 — Cambiar el estado productivo

1. Los estados permitidos son en producción, seco, no productivo y fuera del hato.

2. Cada cambio conserva fecha efectiva, motivo, responsable e historial; no se admite más de un cambio por animal y día.

3. Se rechazan cambios incompatibles con ordeños vigentes.

### PB-11 — Aplicar permisos por rol

1. Administrador gestiona usuarios, animales, estados, ordeños, correcciones, umbrales y auditoría.

2. Operario registra ordeños y consulta; Propietario solo consulta.

3. La API rechaza operaciones no autorizadas sin cambios persistidos; ocultar botones no sustituye esta validación.

### HT-02 — Garantizar integridad y auditoría transaccional

1. Se aplican identificadores únicos, claves foráneas y validaciones coherentes de fechas y cantidades.

2. Datos, auditoría y efectos asociados se confirman o revierten en una sola transacción.

3. La auditoría registra entidad, acción, usuario, fecha, valores anteriores y nuevos y motivo cuando corresponde.

### Definition of Done del equipo

Una historia está terminada cuando sus criterios de aceptación están comprobados, el código está integrado, las pruebas pasan, existe revisión de otro integrante, la documentación está actualizada, el incremento puede demostrarse y no quedan defectos críticos abiertos. El Product Owner acepta o rechaza cada historia en la demostración. El estado Done del tablero debe coincidir con esa evidencia.

## 3. Resultados del corte y límites

Se revisó main en f2bdcce. El PR #41 integra el rediseño y el PR #42 integra animales, estados y auditoría. Durante la preparación reproducible se detectaron dos bloqueos: faltaba GET /api/v1/animales y el frontend no enviaba el motivo de desactivación que exige el backend nuevo. La rama de esta entrega añade el listado paginado con búsqueda y estado efectivo, y el motivo obligatorio en la confirmación. Su integración y revisión de compañero deben completarse antes de tratarla como versión final del corte.

| Historia | Evidencia disponible | Condición pendiente para cierre completo |
|---|---|---|
| HT-01 | Hash adaptativo, sesión, CSRF y rechazo de peticiones no autorizadas. | El entorno local usa HTTP. Falta evidencia de despliegue HTTPS y cookies Secure en ese entorno. |
| PB-01 | Login válido/inválido, logout y caducidad a 30 minutos. La prueba acelera el caso ajustando ultimo_uso de una sesión sintética. | Revisión del equipo y aceptación en vivo. |
| PB-02 | Alta, edición, unicidad, inactividad y permisos. Se corrige el envío de motivo requerido. | Integrar y revisar la corrección de motivo antes de la demo final. |
| PB-03 | Alta, fechas, normalización, auditoría y tabla con búsqueda/filtro. | Integrar y revisar el endpoint de listado añadido en esta entrega. |
| PB-04 | Cambio de estado, versión, historial, duplicado diario e incompatibilidad con ordeño existente. | La UI no permite fuera_del_hato; se delegó a PB-06. Falta ratificar ese recorte frente al criterio original. La integración de ordeños sigue parcial. |
| PB-11 | Servidor rechaza gestión de usuarios y alta de animales a Operario/Propietario; ambos consultan animales. | Los permisos de ordeños, correcciones y umbrales corresponden a módulos futuros. Separar aceptación del corte y cierre total. |
| HT-02 | Restricciones, transacciones, auditoría consultable y protección de registros; suite incluye integridad y migraciones. | La historia se planificó para sprints 1 y 2. Revisar el alcance global antes de cerrarla completa. |

Pruebas disponibles: suite backend de main con 121 aprobadas y 1 fallo esperado; dos nuevas regresiones de listado aprobadas. El fallo esperado registra que POST /ordenos todavía no consulta el estado productivo del animal (PB-07). El script de esta entrega verifica siete secciones contra FastAPI y SQLite temporales. Frontend: 6 pruebas unitarias y 7 pruebas de navegador; además se verificaron alta/listado/cambio de estado y desactivación con motivo desde el navegador contra la API local.

La documentación interna existente del código contiene comentarios y docstrings en español. El nuevo script y las nuevas funciones de integración están documentados en inglés. La exigencia de documentación del código en inglés sigue pendiente de una revisión global, preservando los textos de interfaz en español.

## 4. Trazabilidad y reparto

| Integrante | Trabajo y subtareas | Evidencia de código |
|---|---|---|
| Franky Marin (@Franky0010) | Sesión, usuarios, seguridad y auditoría de usuarios; #27, #29, #31, #36, #38. | Commit 4995c63 (app), c214920 (pruebas), 09df377 (regresión de último administrador). |
| Juan Manuel Alvarez (@juanalvarez6) | Integridad, animales, estados y auditoría; #33, #35, #37. | PR #42; commits 213236c, 577186e, 8fe6de0, 0bd4e93. |
| Juan Diego (@Juanloaiza25) | Frontend, contrato, integración y rediseño; #26, #28, #30, #32, #34. | PR #39 (d915c32), PR #40, PR #41 (db49bda). |

Los commits de los tres integrantes existen. Varios mensajes antiguos de Franky y Juan Diego no incluyen el ID de historia requerido por la consigna. Los enlaces anteriores reconstruyen la relación, pero no corrigen esos mensajes retroactivamente. Los nuevos commits deben incluir IDs. La Nota 1 identifica al tercer autor como Juan Diego Niño y el perfil GitHub como Juan Diego Loaiza; confirmar el nombre académico antes de entregar.

### Enlaces de evidencia

- Repositorio: https://github.com/Franky0010/Sistema-de-Gestion-de-Ganaderia-Lechera
- Tablero público: https://github.com/users/Franky0010/projects/2
- Frontend y contrato: https://github.com/Franky0010/Sistema-de-Gestion-de-Ganaderia-Lechera/pull/39
- Responsables del contrato: https://github.com/Franky0010/Sistema-de-Gestion-de-Ganaderia-Lechera/pull/40
- Rediseño: https://github.com/Franky0010/Sistema-de-Gestion-de-Ganaderia-Lechera/pull/41
- Animales e integridad: https://github.com/Franky0010/Sistema-de-Gestion-de-Ganaderia-Lechera/pull/42

## 5. Tablero y corte de respaldo

La configuración consultada indica tablero público. El export del 5 de noviembre muestra 35 tarjetas: 20 Done (7 historias y 13 subtareas) y 15 Todo. Se adjuntan docs/evidencia/tablero-2026-11-05.json y .csv con los estados observados, responsables y enlaces. Este corte fue obtenido el mismo día de la revisión; no acredita el respaldo del día anterior solicitado por la consigna.

Las tarjetas PB-04, PB-11, HT-01 y HT-02 requieren reconciliar Done con los límites descritos. PB-02 y PB-03 requieren integrar las correcciones de esta entrega. El equipo debe registrar revisión y evidencia por tarjeta. La asociación propuesta es PR #39/#41 para frontend, commits 4995c63/c214920 para acceso y usuarios, y PR #42 para animales e integridad. Falta comprobar que cada tarjeta tenga esos enlaces en su propio contenido.

## 6. Sustentación y siguiente sprint

Mostrar el producto en vivo en este orden: HT-01, PB-01, PB-02, PB-03, PB-04, PB-11, HT-02. El guion y los comandos completos están en docs/demo-sprint1.md. Usar scripts/demo_sprint1.py --serve para una base temporal con tres roles y dos animales, y --verify para repetir las comprobaciones HTTP. Las capturas solo respaldan revisión visual y no sustituyen la demo.

Decisiones observables durante el trabajo: separar demo visual y API real; definir un contrato /api/v1; utilizar cookies de sesión y CSRF; guardar fechas de negocio locales y auditoría UTC; sumar migración de animales, auditoría consultable y respaldo; rediseñar el acceso y tablas; resolver dos diferencias de integración en la preparación de la review. Sin acta inicial no se puede afirmar cuáles fueron imprevistas; el equipo debe contrastarlo oralmente.

Cuellos de botella observados: los formularios dependían de endpoints aún no fusionados; la API nueva incorporó motivo obligatorio sin adaptación simultánea del cliente; la falta del listado impedía usar la tabla. La disponibilidad individual no se midió, por lo que no se atribuyen retrasos a horas o carga personal.

Para Nota 3: integrar y revisar las correcciones, acordar el cierre parcial de PB-04/PB-11/HT-01/HT-02, implementar PB-05/PB-06 y PB-07 a PB-10, resolver el fallo esperado de estado productivo en ordeños, demostrar HTTPS, traducir documentación interna del código, mantener trazabilidad por ID y registrar capacidad y compromisos antes del sprint.

Antes de sustentar: confirmar los nombres académicos y el Sprint Goal, instalar desde una copia limpia, ejecutar --verify, probar el navegador con los tres roles, revisar los enlaces públicos, guardar un corte con fecha real y asegurar la asistencia de todo el equipo. La aceptación del Product Owner se registra durante la sesión.
