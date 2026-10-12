# Product Backlog

**IS873 LABORATORIO DE SOFTWARE**

**SISTEMA DE GESTIÓN DE GANADERÍA LECHERA**

**Versión:** 1.0  
**Fecha:** 13/10/2026

**Elaborado por:**

- JUAN MANUEL ALVAREZ
- FRANKY MARIN
- JUAN DIEGO NIÑO

Pereira, Risaralda - 2026

[Descargar documento original en Word](product-backlog.docx) · [Volver al proyecto](../README.md)

## Índice

- [1. Propósito del Product Backlog](#seccion-1)
  - [1.1. Convenciones de priorización y estimación](#seccion-1-1)
  - [1.2. Orden de implementación](#seccion-1-2)
- [2. Épicas](#seccion-2)
  - [2.1. Acceso y usuarios](#seccion-2-1)
  - [2.2. Gestión del ganado](#seccion-2-2)
  - [2.3. Producción de leche](#seccion-2-3)
  - [2.4. Reportes e indicadores](#seccion-2-4)
  - [2.5. Alertas](#seccion-2-5)
  - [2.6. Calidad técnica](#seccion-2-6)
- [3. Resumen priorizado](#seccion-3)
- [4. Detalle del Product Backlog](#seccion-4)
  - [4.1. Épica: Acceso y usuarios](#seccion-4-1)
    - [4.1.1. PB-01 — Iniciar y cerrar sesión](#seccion-4-1-1)
    - [4.1.2. PB-02 — Administrar cuentas de usuario](#seccion-4-1-2)
    - [4.1.3. PB-11 — Aplicar permisos por rol](#seccion-4-1-3)
  - [4.2. Épica: Gestión del ganado](#seccion-4-2)
    - [4.2.1. PB-03 — Registrar animales](#seccion-4-2-1)
    - [4.2.2. PB-04 — Cambiar el estado productivo](#seccion-4-2-2)
    - [4.2.3. PB-05 — Consultar ficha e historial del animal](#seccion-4-2-3)
    - [4.2.4. PB-06 — Registrar la salida del rebaño](#seccion-4-2-4)
  - [4.3. Épica: Producción de leche](#seccion-4-3)
    - [4.3.1. PB-07 — Registrar un ordeño](#seccion-4-3-1)
    - [4.3.2. PB-08 — Validar cantidades y duplicados](#seccion-4-3-2)
    - [4.3.3. PB-09 — Calcular producción, descarte y disponibilidad](#seccion-4-3-3)
    - [4.3.4. PB-10 — Corregir, anular o reactivar ordeños](#seccion-4-3-4)
  - [4.4. Épica: Reportes e indicadores](#seccion-4-4)
    - [4.4.1. PB-12 — Consultar producción por animal y período](#seccion-4-4-1)
    - [4.4.2. PB-13 — Comparar dos períodos](#seccion-4-4-2)
    - [4.4.3. PB-14 — Visualizar indicadores y cobertura de turnos](#seccion-4-4-3)
    - [4.4.4. PB-15 — Consultar reportes filtrados](#seccion-4-4-4)
  - [4.5. Épica: Alertas](#seccion-4-5)
    - [4.5.1. PB-16 — Detectar disminuciones de producción](#seccion-4-5-1)
    - [4.5.2. PB-17 — Configurar el umbral de alertas](#seccion-4-5-2)
  - [4.6. Épica: Calidad técnica](#seccion-4-6)
    - [4.6.1. HT-01 — Implementar seguridad de autenticación y sesión](#seccion-4-6-1)
    - [4.6.2. HT-02 — Garantizar integridad y auditoría transaccional](#seccion-4-6-2)
    - [4.6.3. HT-03 — Asegurar usabilidad y compatibilidad](#seccion-4-6-3)
    - [4.6.4. HT-04 — Cumplir arquitectura y metas de rendimiento](#seccion-4-6-4)
    - [4.6.5. HT-05 — Verificar calidad y preparar el despliegue](#seccion-4-6-5)
- [5. Propuesta inicial de sprints](#seccion-5)
  - [5.1. Sprint 1 — Acceso, usuarios y animales](#seccion-5-1)
  - [5.2. Sprint 2 — Ordeños, salidas y trazabilidad](#seccion-5-2)
  - [5.3. Sprint 3 — Consultas, indicadores y alertas](#seccion-5-3)
  - [5.4. Sprint 4 — Integración, rendimiento y despliegue](#seccion-5-4)
- [6. Criterios de gestión](#seccion-6)
  - [6.1. Definición de listo (Definition of Ready)](#seccion-6-1)
  - [6.2. Definición de terminado (Definition of Done)](#seccion-6-2)
  - [6.3. Reglas de actualización](#seccion-6-3)

<a name="seccion-1"></a>

## 1. Propósito del Product Backlog

Este documento transforma los requisitos aprobados del Sistema de Gestión de Ganadería Lechera en elementos priorizados y verificables para su implementación. El backlog mantiene el alcance del MVP definido en el documento de planteamiento y diseño; no incorpora exportaciones, sanidad, reproducción, sensores, operación sin conexión ni otros componentes excluidos.

<a name="seccion-1-1"></a>

### 1.1. Convenciones de priorización y estimación

La prioridad utiliza MoSCoW. Todos los requisitos funcionales RF01–RF13 son Must del MVP. Los requisitos no funcionales RNF01–RNF10 se incorporan como condiciones de aceptación e historias técnicas obligatorias. Las estimaciones usan puntos de historia de la serie Fibonacci y son una base inicial que deberá revisarse durante el refinamiento con el equipo.

<a name="seccion-1-2"></a>

### 1.2. Orden de implementación

El orden considera valor, riesgo y dependencias: primero seguridad, acceso y datos maestros; después captura y trazabilidad; luego consultas, indicadores y alertas; finalmente integración, rendimiento, pruebas y despliegue.

<a name="seccion-2"></a>

## 2. Épicas

<a name="seccion-2-1"></a>

### 2.1. Acceso y usuarios

Autenticación, administración de cuentas y autorización por rol.

<a name="seccion-2-2"></a>

### 2.2. Gestión del ganado

Registro de animales, estados, historial y salidas del rebaño.

<a name="seccion-2-3"></a>

### 2.3. Producción de leche

Captura, validación, cálculo y corrección de ordeños.

<a name="seccion-2-4"></a>

### 2.4. Reportes e indicadores

Consultas por período, comparaciones, indicadores y reportes internos.

<a name="seccion-2-5"></a>

### 2.5. Alertas

Configuración y generación de alertas internas por disminución de producción.

<a name="seccion-2-6"></a>

### 2.6. Calidad técnica

Seguridad, integridad, auditoría, usabilidad, arquitectura, rendimiento y pruebas.

<a name="seccion-3"></a>

## 3. Resumen priorizado

1\. PB-01 — Iniciar y cerrar sesión | Must | 5 SP | Acceso y usuarios

2\. PB-02 — Administrar cuentas de usuario | Must | 5 SP | Acceso y usuarios

3\. PB-03 — Registrar animales | Must | 8 SP | Gestión del ganado

4\. PB-04 — Cambiar el estado productivo | Must | 5 SP | Gestión del ganado

5\. PB-05 — Consultar ficha e historial del animal | Must | 5 SP | Gestión del ganado

6\. PB-06 — Registrar la salida del rebaño | Must | 5 SP | Gestión del ganado

7\. PB-07 — Registrar un ordeño | Must | 8 SP | Producción de leche

8\. PB-08 — Validar cantidades y duplicados | Must | 5 SP | Producción de leche

9\. PB-09 — Calcular producción, descarte y disponibilidad | Must | 3 SP | Producción de leche

10\. PB-10 — Corregir, anular o reactivar ordeños | Must | 8 SP | Producción de leche

11\. PB-11 — Aplicar permisos por rol | Must | 5 SP | Acceso y usuarios

12\. PB-12 — Consultar producción por animal y período | Must | 5 SP | Reportes e indicadores

13\. PB-13 — Comparar dos períodos | Must | 5 SP | Reportes e indicadores

14\. PB-14 — Visualizar indicadores y cobertura de turnos | Must | 5 SP | Reportes e indicadores

15\. PB-15 — Consultar reportes filtrados | Must | 5 SP | Reportes e indicadores

16\. PB-16 — Detectar disminuciones de producción | Must | 8 SP | Alertas

17\. PB-17 — Configurar el umbral de alertas | Must | 3 SP | Alertas

18\. HT-01 — Implementar seguridad de autenticación y sesión | Must | 8 SP | Calidad técnica

19\. HT-02 — Garantizar integridad y auditoría transaccional | Must | 8 SP | Calidad técnica

20\. HT-03 — Asegurar usabilidad y compatibilidad | Must | 5 SP | Calidad técnica

21\. HT-04 — Cumplir arquitectura y metas de rendimiento | Must | 8 SP | Calidad técnica

22\. HT-05 — Verificar calidad y preparar el despliegue | Must | 8 SP | Calidad técnica

<a name="seccion-4"></a>

## 4. Detalle del Product Backlog

<a name="seccion-4-1"></a>

### 4.1. Épica: Acceso y usuarios

<a name="seccion-4-1-1"></a>

#### 4.1.1. PB-01 — Iniciar y cerrar sesión

**Épica:** Acceso y usuarios

**Fuente:** RF01, RNF01

**Historia de usuario:** Como usuario activo, quiero iniciar y cerrar sesión con correo electrónico y contraseña, para acceder únicamente a las funciones permitidas por mi rol.

**Criterios de aceptación:**

1\. El sistema acepta credenciales válidas de una cuenta activa y rechaza credenciales inválidas o cuentas inactivas.

2\. La sesión expira después de 30 minutos de inactividad y las solicitudes posteriores son rechazadas.

3\. Al cerrar sesión se invalida la sesión vigente y no se exponen credenciales en la interfaz ni en los registros.

**Prioridad:** Must

**Estimación inicial:** 5 puntos de historia

**Dependencias:** HT-01, PB-12

<a name="seccion-4-1-2"></a>

#### 4.1.2. PB-02 — Administrar cuentas de usuario

**Épica:** Acceso y usuarios

**Fuente:** RF01, RF11

**Historia de usuario:** Como administrador, quiero crear, actualizar y desactivar cuentas, asignando los roles Administrador, Operario o Propietario, para controlar quién utiliza el sistema sin perder el historial.

**Criterios de aceptación:**

1\. El correo electrónico es único y se validan nombre, contraseña y rol.

2\. Una cuenta desactivada no puede iniciar sesión y sus registros históricos se conservan.

3\. Operarios y propietarios no pueden administrar cuentas.

**Prioridad:** Must

**Estimación inicial:** 5 puntos de historia

**Dependencias:** PB-01, HT-01

<a name="seccion-4-1-3"></a>

#### 4.1.3. PB-11 — Aplicar permisos por rol

**Épica:** Acceso y usuarios

**Fuente:** RF11

**Historia de usuario:** Como propietario del sistema, quiero aplicar permisos en cada operación según el rol vigente, para evitar acciones no autorizadas.

**Criterios de aceptación:**

1\. Administrador gestiona usuarios, animales, estados, ordeños, correcciones, umbrales y auditoría.

2\. Operario registra ordeños y consulta; Propietario solo consulta.

3\. La API rechaza operaciones no autorizadas sin cambios persistidos; ocultar botones no sustituye esta validación.

**Prioridad:** Must

**Estimación inicial:** 5 puntos de historia

**Dependencias:** PB-01, PB-02, HT-01

<a name="seccion-4-2"></a>

### 4.2. Épica: Gestión del ganado

<a name="seccion-4-2-1"></a>

#### 4.2.1. PB-03 — Registrar animales

**Épica:** Gestión del ganado

**Fuente:** RF02

**Historia de usuario:** Como administrador, quiero registrar un animal con su identificación y estado inicial, para disponer de una ficha única y trazable.

**Criterios de aceptación:**

1\. Se exige arete, raza, procedencia, fecha de ingreso, nacimiento o edad estimada y estado inicial; el nombre es opcional.

2\. El arete se normaliza sin espacios extremos, no distingue mayúsculas y no puede repetirse ni reutilizarse.

3\. Se rechazan fechas futuras o un nacimiento posterior al ingreso y la creación queda auditada.

**Prioridad:** Must

**Estimación inicial:** 8 puntos de historia

**Dependencias:** PB-01, PB-12, HT-02

<a name="seccion-4-2-2"></a>

#### 4.2.2. PB-04 — Cambiar el estado productivo

**Épica:** Gestión del ganado

**Fuente:** RF02

**Historia de usuario:** Como administrador, quiero cambiar el estado de un animal con fecha efectiva y motivo, para conservar la evolución real del hato.

**Criterios de aceptación:**

1\. Los estados permitidos son en producción, seco, no productivo y fuera del hato.

2\. Cada cambio conserva fecha efectiva, motivo, responsable e historial; no se admite más de un cambio por animal y día.

3\. Se rechazan cambios incompatibles con ordeños vigentes.

**Prioridad:** Must

**Estimación inicial:** 5 puntos de historia

**Dependencias:** PB-03, HT-02

<a name="seccion-4-2-3"></a>

#### 4.2.3. PB-05 — Consultar ficha e historial del animal

**Épica:** Gestión del ganado

**Fuente:** RF03

**Historia de usuario:** Como usuario autorizado, quiero consultar la ficha y el historial productivo de un animal, para analizar su evolución aun después de su salida del hato.

**Criterios de aceptación:**

1\. Administrador, Operario y Propietario pueden buscar por arete o identificador.

2\. El historial incluye estados, salidas, ordeños, responsables, correcciones y anulaciones.

3\. La auditoría administrativa completa solo está disponible para el administrador y no se muestran credenciales ni datos de sesión.

**Prioridad:** Must

**Estimación inicial:** 5 puntos de historia

**Dependencias:** PB-03, PB-04, PB-07, PB-10

<a name="seccion-4-2-4"></a>

#### 4.2.4. PB-06 — Registrar la salida del rebaño

**Épica:** Gestión del ganado

**Fuente:** RF12

**Historia de usuario:** Como administrador, quiero registrar la salida de un animal mediante el estado fuera del hato, para cerrar su permanencia sin eliminar el historial.

**Criterios de aceptación:**

1\. Se exige tipo de salida —venta, muerte, descarte, robo o traslado—, fecha efectiva y motivo; las observaciones son opcionales.

2\. La salida se guarda en ESTADO\_ANIMAL y la fecha\_desde corresponde a la fecha efectiva.

3\. Se rechazan animales ya retirados y salidas retroactivas incompatibles con ordeños vigentes.

**Prioridad:** Must

**Estimación inicial:** 5 puntos de historia

**Dependencias:** PB-03, PB-04, PB-10

<a name="seccion-4-3"></a>

### 4.3. Épica: Producción de leche

<a name="seccion-4-3-1"></a>

#### 4.3.1. PB-07 — Registrar un ordeño

**Épica:** Producción de leche

**Fuente:** RF04

**Historia de usuario:** Como operario o administrador, quiero registrar producción y descarte por animal, fecha y turno, para mantener la producción diaria centralizada.

**Criterios de aceptación:**

1\. Se registran animal, fecha, turno mañana o tarde, litros producidos, litros descartados y observaciones opcionales.

2\. El responsable y la fecha de creación se obtienen de la sesión y del servidor y no son editables desde el cliente.

3\. El ordeño y su auditoría se guardan en una sola transacción y actualizan indicadores y alertas.

**Prioridad:** Must

**Estimación inicial:** 8 puntos de historia

**Dependencias:** PB-01, PB-03, PB-04, PB-08, HT-02

<a name="seccion-4-3-2"></a>

#### 4.3.2. PB-08 — Validar cantidades y duplicados

**Épica:** Producción de leche

**Fuente:** RF05

**Historia de usuario:** Como usuario que registra un ordeño, quiero recibir validaciones claras antes de guardar, para evitar datos inconsistentes o duplicados.

**Criterios de aceptación:**

1\. Producción y descarte son valores finitos, no negativos y con máximo dos decimales; descarte no supera producción.

2\. Solo existe un registro por animal, fecha y turno, incluso ante solicitudes concurrentes y aunque haya sido anulado.

3\. Cero litros es válido; un turno ausente no equivale a cero; cualquier error evita escrituras parciales.

**Prioridad:** Must

**Estimación inicial:** 5 puntos de historia

**Dependencias:** PB-03, PB-04, HT-02

<a name="seccion-4-3-3"></a>

#### 4.3.3. PB-09 — Calcular producción, descarte y disponibilidad

**Épica:** Producción de leche

**Fuente:** RF06

**Historia de usuario:** Como usuario autorizado, quiero obtener totales precisos de producción, descarte y volumen disponible, para conocer el volumen aprovechable.

**Criterios de aceptación:**

1\. Volumen disponible se calcula como producción menos descarte.

2\. Los cálculos usan únicamente ordeños vigentes y excluyen los anulados.

3\. Los litros se muestran con hasta dos decimales y se almacenan como centilitros enteros.

**Prioridad:** Must

**Estimación inicial:** 3 puntos de historia

**Dependencias:** PB-07, PB-08

<a name="seccion-4-3-4"></a>

#### 4.3.4. PB-10 — Corregir, anular o reactivar ordeños

**Épica:** Producción de leche

**Fuente:** RF10

**Historia de usuario:** Como administrador, quiero corregir, anular o reactivar un ordeño indicando el motivo, para subsanar errores sin perder trazabilidad.

**Criterios de aceptación:**

1\. Cada cambio exige motivo, permisos vigentes y la versión conocida del registro.

2\. La auditoría conserva valores anteriores y nuevos, responsable y momento, sin modificar creador ni fecha original.

3\. El cambio, la auditoría y los recálculos se confirman juntos o se revierten por completo.

**Prioridad:** Must

**Estimación inicial:** 8 puntos de historia

**Dependencias:** PB-07, PB-08, PB-09, HT-02

<a name="seccion-4-4"></a>

### 4.4. Épica: Reportes e indicadores

<a name="seccion-4-4-1"></a>

#### 4.4.1. PB-12 — Consultar producción por animal y período

**Épica:** Reportes e indicadores

**Fuente:** RF07

**Historia de usuario:** Como usuario autorizado, quiero consultar producción, descarte y disponibilidad por animal y rango de fechas, para seguir la evolución productiva.

**Criterios de aceptación:**

1\. Los tres roles pueden consultar totales y evolución diaria con filtros válidos.

2\. Un rango invertido se rechaza y un período sin registros muestra “Sin datos”.

3\. Los totales y la gráfica coinciden con los ordeños vigentes.

**Prioridad:** Must

**Estimación inicial:** 5 puntos de historia

**Dependencias:** PB-07, PB-09

<a name="seccion-4-4-2"></a>

#### 4.4.2. PB-13 — Comparar dos períodos

**Épica:** Reportes e indicadores

**Fuente:** RF07

**Historia de usuario:** Como usuario autorizado, quiero comparar dos períodos de igual duración, para identificar variaciones de producción.

**Criterios de aceptación:**

1\. Ambos períodos usan los mismos filtros y deben tener igual duración.

2\. Se muestra diferencia absoluta y variación porcentual con la fórmula definida.

3\. Cuando el período de referencia vale cero, el porcentaje aparece como “No calculable”.

**Prioridad:** Must

**Estimación inicial:** 5 puntos de historia

**Dependencias:** PB-12

<a name="seccion-4-4-3"></a>

#### 4.4.3. PB-14 — Visualizar indicadores y cobertura de turnos

**Épica:** Reportes e indicadores

**Fuente:** RF08

**Historia de usuario:** Como usuario autorizado, quiero consultar el promedio diario y la cobertura de turnos, para distinguir datos completos de registros parciales.

**Criterios de aceptación:**

1\. El promedio diario divide la producción del día entre animales distintos con al menos un ordeño vigente.

2\. Se identifica cuáles animales tienen mañana y tarde completas y cuáles presentan días parciales.

3\. Sin registros se muestra “Sin datos” y la ausencia de turno no se contabiliza como cero.

**Prioridad:** Must

**Estimación inicial:** 5 puntos de historia

**Dependencias:** PB-07, PB-09

<a name="seccion-4-4-4"></a>

#### 4.4.4. PB-15 — Consultar reportes filtrados

**Épica:** Reportes e indicadores

**Fuente:** RF09

**Historia de usuario:** Como usuario autorizado, quiero consultar reportes por período, animal y turno, para revisar totales y detalles dentro de la aplicación.

**Criterios de aceptación:**

1\. El reporte permite filtrar por período, animal y turno.

2\. Los totales de producción, descarte y disponibilidad coinciden con los registros vigentes.

3\. Los filtros inválidos se rechazan y los períodos vacíos se presentan claramente; PDF y CSV quedan fuera del MVP.

**Prioridad:** Must

**Estimación inicial:** 5 puntos de historia

**Dependencias:** PB-12, PB-14

<a name="seccion-4-5"></a>

### 4.5. Épica: Alertas

<a name="seccion-4-5-1"></a>

#### 4.5.1. PB-16 — Detectar disminuciones de producción

**Épica:** Alertas

**Fuente:** RF13

**Historia de usuario:** Como usuario autorizado, quiero consultar alertas internas por disminución de producción, para revisar oportunamente variaciones significativas.

**Criterios de aceptación:**

1\. Se compara la producción diaria con el promedio de los siete días calendario anteriores usando producción sin descontar descarte.

2\. Los ocho días deben tener ambos turnos y pertenecer a un intervalo continuo en producción; de lo contrario se informa “Datos incompletos” o “No evaluable”.

3\. Se crea una sola alerta por animal y fecha cuando la disminución alcanza el umbral, mostrando valores y motivo; no constituye diagnóstico.

**Prioridad:** Must

**Estimación inicial:** 8 puntos de historia

**Dependencias:** PB-07, PB-10, PB-14, PB-17

<a name="seccion-4-5-2"></a>

#### 4.5.2. PB-17 — Configurar el umbral de alertas

**Épica:** Alertas

**Fuente:** RF13

**Historia de usuario:** Como administrador, quiero configurar el porcentaje de disminución que activa una alerta, para adaptar el criterio de revisión manteniendo su historial.

**Criterios de aceptación:**

1\. El umbral inicial es 20 % y solo admite valores mayores que 0 y menores o iguales que 100.

2\. El nuevo valor entra en vigencia desde el día siguiente y conserva auditoría.

3\. Los cálculos históricos utilizan la versión del umbral aplicable a cada fecha.

**Prioridad:** Must

**Estimación inicial:** 3 puntos de historia

**Dependencias:** PB-01, PB-11, HT-02

<a name="seccion-4-6"></a>

### 4.6. Épica: Calidad técnica

<a name="seccion-4-6-1"></a>

#### 4.6.1. HT-01 — Implementar seguridad de autenticación y sesión

**Épica:** Calidad técnica

**Fuente:** RNF01

**Historia de usuario:** Como equipo de desarrollo, quiero proteger credenciales, sesiones y operaciones de cambio, para reducir accesos y solicitudes no autorizadas.

**Criterios de aceptación:**

1\. Las contraseñas usan hash adaptativo y los secretos permanecen fuera del repositorio.

2\. El despliegue utiliza HTTPS y cookies HttpOnly, Secure y SameSite.

3\. Las operaciones de cambio incluyen protección CSRF y la API valida usuario activo y permisos.

**Prioridad:** Must

**Estimación inicial:** 8 puntos de historia

**Dependencias:** —

<a name="seccion-4-6-2"></a>

#### 4.6.2. HT-02 — Garantizar integridad y auditoría transaccional

**Épica:** Calidad técnica

**Fuente:** RNF06, RNF07

**Historia de usuario:** Como equipo de desarrollo, quiero aplicar restricciones, claves foráneas, transacciones y auditoría, para evitar datos parciales y conservar trazabilidad.

**Criterios de aceptación:**

1\. Se aplican identificadores únicos, claves foráneas y validaciones coherentes de fechas y cantidades.

2\. Datos, auditoría y efectos asociados se confirman o revierten en una sola transacción.

3\. La auditoría registra entidad, acción, usuario, fecha, valores anteriores y nuevos y motivo cuando corresponde.

**Prioridad:** Must

**Estimación inicial:** 8 puntos de historia

**Dependencias:** HT-01

<a name="seccion-4-6-3"></a>

#### 4.6.3. HT-03 — Asegurar usabilidad y compatibilidad

**Épica:** Calidad técnica

**Fuente:** RNF03, RNF09

**Historia de usuario:** Como usuario, quiero utilizar la aplicación desde computador o móvil y navegar con claridad, para completar los flujos sin instalación local.

**Criterios de aceptación:**

1\. La interfaz se adapta a computadores y dispositivos móviles.

2\. Los controles tienen etiquetas claras, admiten navegación por teclado y muestran errores junto al campo.

3\. Los flujos principales funcionan en versiones modernas de Chrome, Firefox y Edge.

**Prioridad:** Must

**Estimación inicial:** 5 puntos de historia

**Dependencias:** PB-07, PB-12

<a name="seccion-4-6-4"></a>

#### 4.6.4. HT-04 — Cumplir arquitectura y metas de rendimiento

**Épica:** Calidad técnica

**Fuente:** RNF02, RNF04, RNF05, RNF08

**Historia de usuario:** Como equipo de desarrollo, quiero mantener una solución medible, modular y preparada para evolución, para facilitar pruebas, mantenimiento y crecimiento.

**Criterios de aceptación:**

1\. Rutas, servicios de negocio y repositorios están separados; la API se documenta con OpenAPI y las versiones quedan fijadas.

2\. Guardar ordeños y listar animales tarda menos de 2 s en P95; reportes de hasta 90 días, menos de 3 s en P95, sin latencia de Internet.

3\. El prototipo alcanza 99 % de respuestas exitosas durante la ventana acordada de 8 horas y permite evaluar migración de SQLite a PostgreSQL.

**Prioridad:** Must

**Estimación inicial:** 8 puntos de historia

**Dependencias:** PB-07, PB-15, HT-02

<a name="seccion-4-6-5"></a>

#### 4.6.5. HT-05 — Verificar calidad y preparar el despliegue

**Épica:** Calidad técnica

**Fuente:** RNF10

**Historia de usuario:** Como equipo de desarrollo, quiero documentar y ejecutar pruebas para cada elemento del MVP, para entregar una versión integrada sin defectos críticos.

**Criterios de aceptación:**

1\. Cada funcionalidad cuenta con pruebas documentadas y aprobadas antes de marcarse como terminada.

2\. El código pasa revisión, la documentación queda actualizada y el incremento se demuestra integrado.

3\. El MVP valida todos los RNF y no presenta defectos críticos abiertos.

**Prioridad:** Must

**Estimación inicial:** 8 puntos de historia

**Dependencias:** Todos los elementos del MVP

<a name="seccion-5"></a>

## 5. Propuesta inicial de sprints

<a name="seccion-5-1"></a>

### 5.1. Sprint 1 — Acceso, usuarios y animales

HT-01, PB-01, PB-02, PB-03, PB-04, PB-11 y comienzo de HT-02.

<a name="seccion-5-2"></a>

### 5.2. Sprint 2 — Ordeños, salidas y trazabilidad

PB-06, PB-07, PB-08, PB-09, PB-10, PB-05 y continuación de HT-02.

<a name="seccion-5-3"></a>

### 5.3. Sprint 3 — Consultas, indicadores y alertas

PB-12, PB-13, PB-14, PB-15, PB-17, PB-16 y HT-03.

<a name="seccion-5-4"></a>

### 5.4. Sprint 4 — Integración, rendimiento y despliegue

HT-04, HT-05, correcciones de integración, validación de los RNF y demostración del MVP.

La asignación supone ciclos de dos semanas, como propone el documento de planteamiento. Debe ajustarse a la capacidad real del equipo y al calendario académico; los puntos de historia no representan horas.

<a name="seccion-6"></a>

## 6. Criterios de gestión

<a name="seccion-6-1"></a>

### 6.1. Definición de listo (Definition of Ready)

Un elemento está listo para entrar a un sprint cuando su objetivo y valor están claros, tiene criterios de aceptación verificables, dependencias identificadas, datos de prueba disponibles, estimación acordada y no mantiene decisiones funcionales bloqueantes.

<a name="seccion-6-2"></a>

### 6.2. Definición de terminado (Definition of Done)

Un elemento se considera terminado cuando cumple sus criterios de aceptación, cuenta con pruebas aprobadas, revisión de código, documentación actualizada, integración con los módulos relacionados y demostración funcional. El incremento no debe dejar defectos críticos abiertos.

<a name="seccion-6-3"></a>

### 6.3. Reglas de actualización

El Product Owner prioriza y aclara los elementos; el equipo estima y actualiza el estado. Cualquier cambio de alcance debe conservar la referencia al requisito de origen y registrar su justificación. Los elementos fuera del MVP se refinan únicamente después de completar los Must.
