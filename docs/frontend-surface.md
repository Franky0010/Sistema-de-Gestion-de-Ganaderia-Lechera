# Sprint 1 — superficie operativa

Modo: Operate. Rediseño aprobado el 5 de noviembre de 2026: acceso B y tablas A, exploración grounded con seed `945328c5`. Los wireframes conservan autoridad funcional, no visual.

## Direction contract

THESIS: encontrar y actualizar registros del hato con información legible y acciones explícitas.

OWN-WORLD: superficies blancas, verde bosque, navegación carbón y tabla plana compacta. Tipografía de sistema y numerales tabulares. Tokens y componentes en `DESIGN.md`.

STORY: acceder, identificar el registro, completar la tarea y recibir confirmación. Los datos sintéticos se identifican en modo demo. El rediseño conserva el comportamiento existente de la API.

FIRST VIEWPORT: acceso con paisaje al 40% y formulario al 60%; en móvil, foto de 160px sobre el formulario. El espacio de trabajo usa barra lateral carbón, título, acción principal verde, filtros y tabla sin tarjeta envolvente. En móvil, navegación horizontal y registros apilados. Formularios en páginas dedicadas.

FORM: SVG locales de Google Material Symbols Outlined en `frontend/src/assets/icons`, con licencia Apache-2.0; no emojis. Fotografía decorativa generada en `frontend/src/assets/pasture.webp`, con prompt y fecha en `pasture.webp.json`; no es una imagen de la finca del usuario.

FINISH: revisión final Ship. Inspección inicial de 13 capturas en cinco anchos; confirmación posterior limitada a `animales-nuevo-320.png` y `usuarios-768.png`, verificando la corrección del texto de edad y el ajuste de correos y acciones apiladas. Sin problemas materiales restantes en ese alcance.

## Evidencia de entrega

Capturas de acceso, animales, usuarios y formularios en `.impeccable/review/redesign`, a 320, 390, 768, 1280 y 1440px. Compilación final, 6 pruebas unitarias y 7 pruebas de navegador aprobadas. Verificación con backend real: acceso, gestión de usuarios (crear, consultar, editar y desactivar), duplicados, campos obligatorios, caducidad de sesión y cuenta inactiva.

La revisión visual acredita las superficies inspeccionadas. Estas comprobaciones funcionales no constituyen una auditoría completa de seguridad ni certifican todos los flujos del backend.
