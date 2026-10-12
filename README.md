# PoC —Registro de ordeños sin duplicados ni escrituras parciales

Prueba de concepto del **Sistema de Gestión de Ganadería Lechera**
(Laboratorio de Software IS873 · Universidad Tecnológica de Pereira).

Autores: Juan Manuel Alvarez · Franky Marin · Juan Diego Niño

---

## 1. ¿Qué riesgo técnico comprueba?

El sistema debe garantizar que **no existan dos ordeños para el mismo animal, fecha y turno**
(RN03 / RF05), incluso si dos personas guardan el mismo registro al mismo tiempo, y que el
ordeño y su auditoría se guarden **juntos o no se guarden** (RF04 / RNF06).

Este riesgo es crítico porque el MVP usa **SQLite**, que permite una sola escritura a la vez.
Una validación del tipo *"consultar si existe y luego insertar"* falla bajo concurrencia
(las dos solicitudes ven que no existe y ambas insertan). La PoC verifica que la solución
planteada en el documento de diseño funciona:

| Decisión de diseño | Dónde está |
|---|---|
| Restricción `UNIQUE (animal_id, fecha, turno)` en la base de datos | `app/models.py` |
| Ordeño + auditoría en **una sola transacción** con `rollback` ante cualquier fallo | `app/service.py` |
| Litros guardados como **centilitros enteros** (12,50 L → 1250 cL) | `app/service.py` |
| `PRAGMA foreign_keys=ON`, modo WAL y espera acotada (`busy_timeout`) | `app/database.py` |
| Duplicado → HTTP **409**; bloqueo persistente → HTTP **503** (recuperable) | `app/main.py` |

## 2. Qué pruebas incluye

Corresponden a la prueba de concepto definida en la sección 4.1 del documento de diseño:

| # | Prueba | Resultado esperado |
|---|---|---|
| 1 | Creación válida (y caso de 0 litros) | Quedan 1 ordeño y 1 auditoría |
| 2a | 2 solicitudes HTTP simultáneas con la misma clave, repetidas 50 veces con claves nuevas | Cada repetición: un `201` y un `409`. Al final 50 ordeños y 50 auditorías |
| 2b | 8 hilos simultáneos con la misma clave | 1 éxito y 7 `DuplicadoError`; 1 ordeño en BD |
| 3 | Fallo simulado antes del `commit` | 0 ordeños y 0 auditorías nuevos (rollback completo) |
| 4 | Cantidades inválidas: negativas, descarte > producción, más de 2 decimales, texto, `NaN` | Respuesta `422` y nada persistido |
| 5 | Animal inexistente | `404` y nada persistido |

## 3. Estructura

```
poc-ganaderia-lechera/
├── app/
│   ├── database.py   # engine SQLite + PRAGMA
│   ├── models.py     # Animal, Ordeno, Auditoria
│   ├── service.py    # reglas de negocio y transacción
│   └── main.py       # API FastAPI (POST /animales, POST /ordenos)
├── tests/
│   └── test_poc.py   # pruebas de la PoC
├── requirements.txt
├── pytest.ini
└── README.md
```

## 4. Cómo ejecutar

Requisitos: Python 3.10 o superior.

```bash
git clone <URL-DEL-REPOSITORIO>
cd poc-ganaderia-lechera

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

pytest -v -s
```

### (Opcional) Probar la API manualmente

```bash
uvicorn app.main:app --reload
```

Documentación interactiva en <http://127.0.0.1:8000/docs>. Con `curl`:

```bash
# Crear un animal
curl -X POST localhost:8000/animales -H "Content-Type: application/json" \
     -d '{"arete": "V-001", "nombre": "Luna"}'

# Registrar un ordeño (el responsable viene de la cabecera X-Usuario)
curl -X POST localhost:8000/ordenos -H "Content-Type: application/json" \
     -H "X-Usuario: operario01" \
     -d '{"animal_id": 1, "fecha": "2026-10-06", "turno": "mañana",
          "litros_producidos": "12.50", "litros_descartados": "0.50"}'
# -> 201. Repetir el mismo comando -> 409 (duplicado)
```

## 5. Resultado esperado vs. resultado obtenido

**Esperado:** todas las pruebas de la tabla del punto 2 pasan.

**Obtenido** *(completar con la ejecución del equipo)*:

| Dato | Valor |
|---|---|
| Fecha de ejecución | |
| Sistema operativo / Python | |
| Versiones (`pip freeze`) | |
| Resultado de `pytest -v -s` | `__ passed, __ failed` |
| Prueba 2a: repeticiones distintas de `[201, 409]` | `__ de 50` |
| Prueba 2b: resultado de los 8 hilos | |
| Prueba 3: ordeños/auditorías tras el fallo | |

Pegar aquí la salida de la consola:

```
(salida de pytest -v -s)
```

## 6. Qué NO valida esta PoC

- Autenticación, sesiones, roles ni permisos: el responsable llega por la cabecera
  `X-Usuario` solo como sustituto (RF01, RF11, RNF01).
- Corrección, anulación y reactivación de ordeños ni control de versión (RF10).
- Estado efectivo del animal (p. ej., rechazar ordeños de un animal no productivo o fuera del hato).
- Validación de fechas futuras o anteriores al ingreso, y zona horaria America/Bogota.
- Cálculo de indicadores, reportes y alertas (RF06–RF09, RF13).
- Rendimiento y carga (RNF04): se usan 2 a 8 solicitudes simultáneas, no los 5 usuarios /
  100.000 ordeños de la prueba de carga.
- Despliegue con HTTPS, respaldos y restauración.
- Migración a PostgreSQL: la PoC solo comprueba que SQLite aguanta este escenario pequeño.
- Interfaz web.

## 7. Conclusión

*(Completar después de ejecutar: ¿se cumplió el riesgo planteado? ¿Apareció algún bloqueo
`503` o comportamiento inesperado? ¿Cambia alguna decisión del diseño, por ejemplo evaluar
PostgreSQL antes?)*

## 8. Relación con la documentación

- Requisitos: RF04, RF05, RF06 (centilitros), RNF06 (integridad), RNF07 (auditoría).
- Casos de uso: CU-02 (Registro y control de ordeños).
- Reglas de negocio: RN02, RN03, RN04.
- Backlog: PB-07, PB-08, HT-02.
