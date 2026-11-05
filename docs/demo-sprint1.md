# Guion reproducible — Sprint Review 1

Demuestra acceso, cuentas, animales, estados, permisos y auditoría con la aplicación real y SQLite temporal. La sesión expirada se reproduce moviendo el último uso de una sesión de prueba 31 minutos atrás. No acredita HTTPS de producción, rendimiento, disponibilidad, módulos futuros ni revisión de código por otro integrante.

## Preparación en otra máquina

Requisitos: Git, Python 3.11+ y Node.js 22.12+. Ejecutar desde una copia del repositorio que incluya esta entrega. La rama de preparación es `docs/nota2-sprint-review1`; si aún no está publicada, utilizar la copia de código entregada por el equipo.

```powershell
cd Sistema-de-Gestion-de-Ganaderia-Lechera
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/demo_sprint1.py --verify
```

El resultado esperado termina en `PASS | Seven sections verified`. Cualquier aserción fallida detiene la ejecución con código de error. Cada ejecución crea una base nueva y elimina sus datos temporales al finalizar. El script configura su propia conexión y no utiliza la base personal del integrante.

Para la demo en vivo, dejar abierta una primera terminal:

```powershell
.\.venv\Scripts\python.exe scripts/demo_sprint1.py --serve
```

En una segunda terminal, desde la raíz del repositorio:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev -- --host localhost --port 5187
```

Abrir http://localhost:5187/ui/. Los puertos 8000 y 5187 deben estar disponibles. Detener una ejecución anterior con Ctrl+C antes de reiniciar. En Linux/macOS usar `.venv/bin/python` y `npm`.

| Cuenta de ejemplo | Rol | Contraseña de demostración |
|---|---|---|
| admin@demo.local | Administrador | Sprint1-Demo2026 |
| operario@demo.local | Operario | Sprint1-Demo2026 |
| propietario@demo.local | Propietario | Sprint1-Demo2026 |

La semilla contiene DEMO-001 (Luna) y DEMO-002 (Estrella), con ingreso dos días antes de la ejecución. Todos los datos y credenciales son sintéticos. Reiniciar `--serve` restablece la semilla. `npm run demo` utiliza un simulador y no es el comando de esta sustentación.

## 1. HT-01 — Seguridad de autenticación y sesión

Antes del acceso, intentar abrir `#/usuarios`: aparece el login. Ejecutar `--verify` muestra el rechazo HTTP 403 de un login enviado sin CSRF y 401 de una consulta sin sesión. Explicar que el servidor almacena hash adaptativo y la cookie es HttpOnly/SameSite. El entorno local HTTP no demuestra el criterio de despliegue HTTPS/Secure.

## 2. PB-01 — Iniciar y cerrar sesión

Introducir una contraseña incorrecta y mostrar el error. Entrar como administrador, recargar y comprobar que permanece la sesión. Salir y comprobar el regreso al login. La sección PB-01 de `--verify` prueba la expiración a 30 minutos mediante un reloj de sesión preparado en la base temporal; esa preparación evita esperar 31 minutos durante la exposición. Volver a entrar para continuar.

## 3. PB-02 — Administrar cuentas

En Usuarios, pulsar Crear usuario y enviar el formulario vacío. Completar nombre, `temporal@demo.local`, contraseña `Sprint1-Demo2026` y rol Operario. Crear otra cuenta con el mismo correo y mostrar el error. Editar la cuenta temporal para asignarle Propietario. Desactivarla, dejando primero el motivo vacío para mostrar la validación, y luego indicar «Terminó la demostración». Mostrar la cuenta inactiva y, después de salir, intentar acceder con ella. Volver al administrador. Conservar las cuentas operario y propietario de la semilla para PB-11.

## 4. PB-03 — Registrar animales

Registrar DEMO-003, nombre Lucero, raza Jersey, procedencia «Demostración», ingreso hoy y nacimiento anterior al ingreso o edad estimada de 36 meses. Elegir En producción. Mostrar el registro en la tabla, buscar su arete y filtrar por estado. Repetir el arete y mostrar la validación. Intentar una fecha futura y mostrar el error. La sección automática también verifica normalización y duplicados.

## 5. PB-04 — Cambiar estado productivo

Usar DEMO-001, que ingresó dos días antes. Elegir Seco con fecha de hoy y un motivo. Guardar y comprobar la tabla. Intentar otro cambio en el mismo día y mostrar el conflicto. El historial se consulta mediante la API; la ficha completa queda en PB-05. `--verify` añade un ordeño sintético mediante el PoC y comprueba el rechazo de un estado incompatible. Explicar que la UI aún delega Fuera del hato a PB-06 y que el PoC de ordeños todavía permite crear ordeños sin validar estado productivo.

## 6. PB-11 — Permisos por rol

Salir y entrar como Operario. Mostrar consulta de animales y ausencia de gestión de usuarios. Intentar `#/usuarios` y comprobar Acceso restringido. Repetir con Propietario. La sección automática verifica además que el servidor rechaza consultar usuarios y crear animales con ambos roles. Los permisos de módulos futuros no forman parte de esta demostración.

## 7. HT-02 — Integridad y auditoría

Entrar nuevamente como administrador. Abrir http://localhost:5187/api/v1/auditoria en el mismo navegador para mostrar el JSON con entidad, acción, responsable y motivo. `--verify` compara los totales antes y después de un alta duplicada y comprueba que no se agrega animal ni auditoría. Para rollback, migraciones y restricciones ejecutar la suite del backend. El procedimiento de respaldo está descrito en el contrato; sus objetivos operativos requieren una medición separada.

## Cierre de la sustentación

Registrar la aceptación o rechazo del docente por historia. Mostrar el tablero y explicar las diferencias entre Done observado y los criterios globales aún pendientes del informe. Confirmar el trabajo que continúa en Nota 3. Todo el equipo debe estar presente; la demo se hace sobre el producto, con las capturas reservadas para evidencia de revisión visual.
