---
name: Ganadería lechera
description: Interfaz operativa clara con verde bosque, registros legibles y acciones explícitas.
colors:
  primary: "#174b3d"
  surface: "#ffffff"
  canvas: "#ffffff"
  sidebar: "#202a28"
  navigation-active: "#345446"
  ink: "#243b32"
  muted: "#52655b"
  border: "#dce4df"
  focus: "#39856b"
  placeholder: "#5e7365"
  error: "#a32e2a"
typography:
  headline:
    fontFamily: "Segoe UI, system-ui, sans-serif"
    fontSize: "26px"
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  body:
    fontFamily: "Segoe UI, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Segoe UI, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 550
rounded:
  control: "5px"
  input: "7px"
  panel: "12px"
spacing:
  small: "12px"
  medium: "20px"
  large: "28px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "10px 17px"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.panel}"
---

# Design System: Ganadería lechera

## Overview

Dirección aprobada el 5 de noviembre de 2026: verde bosque, superficies blancas y navegación carbón. El usuario eligió acceso B y tablas A durante la exploración grounded con seed `945328c5`. Se conserva la información funcional de los wireframes, no su apariencia.

La jerarquía operativa prioriza título, acción principal, filtros y registros compactos. La fotografía rural aporta contexto al acceso; el espacio de trabajo mantiene superficies planas. Fuente de verdad: `frontend/src/styles.css` y `frontend/src/views.js`.

## Colors

El verde bosque identifica la acción primaria y los controles. La navegación carbón usa texto claro y verde apagado para el enlace activo. Blanco sostiene formularios y tablas; bordes claros separan registros sin encerrar la lista en una tarjeta.

Los estados combinan nombre y color: verde para activo o producción, amarillo para seco y neutro para inactivo o fuera del hato. Rojo identifica errores y acciones de desactivación; el color nunca comunica el estado por sí solo.

## Typography

Segoe UI con respaldo de sistema, cuerpo de 15px y títulos de 26px. El acceso usa un título de 28px y marca de 20px. Etiquetas de formulario de 13px; tablas con cabeceras de 12px y celdas de 14px. Numerales tabulares y ajuste de palabras largas en nombres y correos.

## Layout

Escritorio: barra lateral de 208px y contenido flexible, máximo de 1450px, con relleno de 30px vertical y 32px horizontal. A 1100px la barra ocupa 195px y el relleno del contenido es de 28px. Entre 721px y 900px, las acciones de tabla se apilan y las celdas reducen su relleno horizontal a 10px.

A 720px, la navegación pasa a una franja superior horizontal, los registros se apilan con etiquetas y el contenido tiene márgenes laterales de 16px. Formularios de dos columnas pasan a una; a 1100px el contexto lateral ya se sitúa debajo del formulario.

Acceso B: paisaje al 40% y formulario al 60% en escritorio, con caja de formulario de hasta 392px. A 720px, fotografía superior de 160px y formulario debajo. Esta composición pertenece al acceso, no a todas las pantallas.

## Elevation & Depth

Tablas planas con separadores horizontales. Paneles de formulario con borde fino, sin sombra decorativa. Solo notificaciones y diálogo de confirmación usan sombras difusas; el fondo del diálogo oscurece el contexto.

## Shapes

Botones y etiquetas de estado con radio de 5px; inputs de 7px, navegación de 8px, paneles de 12px y diálogo de 14px. Avatar circular reservado a la cuenta. SVG locales de Google Material Symbols Outlined, tamaño habitual de 20px y color heredado; no emojis.

## Components

- **Botones:** primarios verdes, secundarios blancos con borde y acciones de fila discretas. Altura mínima de 43px; presión con escala .98 y transición de 140ms. Hover solo con puntero fino; movimiento reducido desactiva transiciones y escala.
- **Campos:** altura mínima de 44px, etiqueta visible, ayuda y error asociados mediante `aria-describedby`. La edad estimada usa «Edad estimada al ingreso (meses)» y conserva el ancho disponible en móvil.
- **Navegación:** activo con `aria-current`, cuenta y rol visibles, retorno al inicio de formularios y enlace de salto al contenido.
- **Tablas:** filas compactas, cabeceras discretas, arete y nombre para identificar animales; nombre y correo para usuarios. Búsqueda explícita, filtros y paginación. Las listas no tienen tarjeta envolvente ni símbolos decorativos por fila.
- **Confirmación:** diálogo nativo de desactivación, Cancelar como foco inicial y acción bloqueada durante envío.
- **Acceso:** imagen decorativa `frontend/src/assets/pasture.webp`, generada con IA, con prompt y fecha en `pasture.webp.json`. No representa la finca del usuario. `alt=""` y recorte `object-fit: cover`.
- **Accesibilidad:** foco visible de 3px con separación de 3px; estados de carga, vacío, error y confirmación explícitos. Los SVG decorativos se ocultan a tecnologías de asistencia.

## Do's and Don'ts

- Do mantener una acción principal clara y errores que indiquen cómo corregir el problema.
- Do conservar iconos oficiales locales y su licencia en `frontend/src/assets/icons`.
- Do probar vistas completas en escritorio, tablet y móvil, incluyendo textos largos y formularios.
- Don't introducir gráficas, métricas ni datos de negocio inventados para llenar espacio.
- Don't presentar la imagen generada ni los datos de demostración como información real de la finca.
- Don't modificar el comportamiento de la API para resolver decisiones visuales.
