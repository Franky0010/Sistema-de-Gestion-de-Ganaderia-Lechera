# Ganadería lechera

## Platform
Web adaptable a computador y móvil, para una sola finca y operación en línea.

## Usuarios y tareas
Administrador: usuarios, animales y estados; Operario y Propietario: consulta del hato en esta primera entrega. Los módulos de ordeños, reportes y alertas se desarrollan en sprints posteriores.

## Stack
HTML, Tailwind CSS compilado y JavaScript modular; FastAPI y SQLAlchemy en backend. Se conserva el stack propuesto en el documento del proyecto. Vite es herramienta de desarrollo y compilación, no un framework de interfaz.

## Alcance autorizado
Propuesta de contrato API y frontend del sprint 1: acceso/sesión (#26), usuarios (#28), roles (#30), registro animal (#32), estados (#34). El usuario autorizó proponer endpoints para que sus compañeros implementen el backend. La propuesta no se presenta como un acuerdo ya aprobado.

## Restricciones
No implementar autenticación de producción en el navegador. Cookie HttpOnly y CSRF, 30 minutos de inactividad, permisos validados por servidor. Preservar el PoC existente. No cerrar historias sin integración real, pruebas y revisión de equipo.

## Diseño
El usuario aclara que los wireframes del documento son solo demostrativos y solicita un diseño nuevo, mejorado. Se conserva su información funcional, no su apariencia. Impeccable y Emil Design Engineering orientan el trabajo.

## Decisiones abiertas
El equipo debe revisar rutas y esquemas propuestos, reglas de contraseña y estrategias de conflictos. Las pruebas con datos simulados no acreditan integridad ni autorización del backend real.
