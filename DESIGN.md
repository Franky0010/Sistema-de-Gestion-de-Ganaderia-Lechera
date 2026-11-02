---
name: Ganadería lechera
description: Interfaz operativa clara con verde bosque, registros legibles y acciones explícitas.
colors:
  primary: "#174b3d"
  surface: "#ffffff"
  canvas: "#f5f7f5"
  ink: "#243b32"
  muted: "#52655b"
  border: "#dce4df"
  focus: "#39856b"
  placeholder: "#5e7365"
  error: "#a32e2a"
typography:
  headline:
    fontFamily: "Segoe UI, system-ui, sans-serif"
    fontSize: "clamp(1.75rem, 2.5vw, 2.25rem)"
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
  control: "8px"
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

Dirección aprobada: interfaz clara con verde bosque. El usuario rechazó la apariencia de los wireframes originales; se retienen solo sus funciones. El sistema sirve a tareas repetidas de gestión del hato, con una jerarquía de título, acción principal, filtros y registros.

Las pantallas nuevas deben conservar el carácter operativo: datos legibles, controles reconocibles y confirmaciones precisas. La demo se identifica explícitamente; sus animales y personas no son datos reales de una finca.

## Colors

El verde bosque identifica la acción principal, la marca y la navegación activa. Blanco para superficies de trabajo; fondo neutro ligeramente verdoso para separar el espacio. Tinta y texto secundario mantienen contraste sobre ambos fondos.

Estados productivos usan fondos verdes, amarillos o neutros **junto con su nombre**. Rojo queda reservado a error o desactivación. Nunca comunicar permisos, errores o estado solo con color.

## Typography

Segoe UI y la pila de sistema se eligieron para consistencia operativa y lectura de formularios; no representan una tipografía editorial de marca. Títulos compactos, campos de 13px y cuerpo de 15px. Los datos tabulares utilizan numerales de ancho uniforme. La escala del mensaje de acceso es específica de esa pantalla y no una regla para añadir titulares grandes a todas las vistas.

## Layout

En escritorio, navegación lateral de 230px y área flexible; a 1100px se reduce a 195px. Contenido de máximo 1450px con padding de 40px, reducido a 28px en pantallas intermedias. La cabecera separa ubicación y cuenta.

Formularios dedicados: panel de hasta 760px y explicación lateral de hasta 260px. Campos en dos columnas. A 1100px desaparece la segunda columna de contexto; a 720px la navegación es horizontal, las tablas se apilan por registro y los campos pasan a una columna, con 16px de margen exterior.

## Elevation & Depth

Paneles planos con un borde fino; no combinar borde con sombra decorativa. Solo las notificaciones y la confirmación modal se elevan: sombras difusas con desplazamiento vertical. El fondo del dialog oscurece el contexto para proteger una decisión de desactivación.

## Shapes

Controles de esquinas discretas (8px), inputs (7px), paneles (12px) y diálogo (14px). Las etiquetas de estado son rectángulos suaves de 5px. El avatar circular identifica a la persona; no se usa como contenedor genérico de información. Iconos SVG lineales, coherentes en tamaño y trazo.

## Components

- **Botones:** acción primaria verde, secundarios blancos con borde y acciones de fila discretas. Altura mínima 43px. Feedback de presión escala .98, transición de 140ms; no animar el cambio de páginas.
- **Campos:** etiqueta visible, indicación de obligatoriedad, ayuda y error vinculados por `aria-describedby`. Error junto al campo, foco al primer dato inválido y valores conservados. Inputs de 44px mínimo.
- **Navegación:** activo con fondo verde tenue y `aria-current`. Enlaces de retorno al inicio de formularios. El enlace de salto al contenido enfoca main sin cambiar la ruta hash.
- **Tablas:** cabeceras discretas, separadores horizontales, identificación de animal con arete y nombre. En móvil, cada celda muestra su etiqueta. Buscar y filtrar son operaciones explícitas y paginadas.
- **Confirmación:** dialog nativo para desactivar una cuenta, Cancelar como foco inicial, botón de acción bloqueado durante envío.
- **Estados:** carga, vacío, error, validación y confirmación. Error 401 elimina datos privados de la pantalla. La cuenta y el rol siempre están visibles dentro del espacio de trabajo.
- **Accesibilidad:** foco visible de 3px con separación de 3px, preferencia de movimiento reducido, selección/caret/scrollbars del sistema visual. Hover solo para puntero fino. Placeholder verificado en 5.10:1 sobre blanco.

## Do's and Don'ts

- Do mantener una acción principal clara y mensajes que expliquen cómo corregir el problema.
- Do usar el mismo vocabulario del contrato y del backlog, con acentos en la interfaz.
- Do probar capturas de vistas completas, no estados de carga, en escritorio y móvil.
- Don't introducir gráficas, métricas ni datos de negocio inventados para llenar espacio.
- Don't añadir controles de módulos futuros sin una acción disponible.
- Don't presentar permisos visuales o respuestas simuladas como seguridad del servidor.

Fuente de verdad: `frontend/src/styles.css` y `frontend/src/views.js`. Revisión final limitada al frontend y sus correcciones: apto para compartir e integrar; no acredita el backend real.
