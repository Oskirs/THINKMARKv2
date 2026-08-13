# Guía de personalización visual de THINKMARK

La identidad visual está separada del recorrido, los datos y los servicios. Estos
cambios pueden hacerse sin modificar el código base de `app.py` o `src/`.

## 1. Sustituir el logo

1. Copiar el logo definitivo en `assets/` en formato SVG, PNG o JPG.
2. Abrir `config/brand.json`.
3. Cambiar el valor de `logo_path`, por ejemplo:

```json
"logo_path": "assets/logo_thinkmark.svg"
```

Se recomienda una versión horizontal, fondo transparente y proporción aproximada
de 4:1. El encabezado principal admite hasta 220 px de ancho y el lateral 180 px.

## 2. Cambiar colores de marca

La configuración inicial usa la paleta observada en los activos públicos oficiales
de la UAG consultados el 10 de agosto de 2026:

Fuente de referencia: `https://www.uag.mx/` y su hoja de estilos pública vigente en
la fecha de consulta.

- Tinto principal: `#76232F`.
- Tinto oscuro: `#641723`.
- Naranja de acento: `#ED8B00`.
- Azul profundo: `#1A1E40`.

Esta aplicación de color debe validarse con el área institucional correspondiente
antes de una publicación definitiva; no sustituye un manual de identidad autorizado.

Editar en `config/brand.json`:

- `primary`: acciones y énfasis.
- `primary_dark`: textos o estados intensos.
- `accent`: oportunidades y elementos complementarios.
- `ink`: texto principal.
- `muted`: texto secundario.
- `surface`: tarjetas.
- `canvas`: fondo general.
- `border`: divisiones y contornos.
- `success` y `warning`: estados semánticos.

Para que los controles nativos de Streamlit coincidan, actualizar también los cinco
valores de `[theme]` en `.streamlit/config.toml`. Son archivos de configuración, no
lógica de la aplicación.

## 3. Cambiar nombre, lema o tipografía

En `config/brand.json` pueden modificarse `app_name`, `tagline` y `font_family`.
Si se utiliza una fuente web no instalada, deberá agregarse posteriormente su carga
en una hoja de estilos; para el MVP se recomiendan fuentes del sistema.

## 4. Cambiar el caso y los textos demostrativos

El caso está en `data/fixtures/demo_case.json`. Puede duplicarse para crear variantes.
No deben introducirse datos personales reales en los fixtures ni incluir claves,
contraseñas o tokens.

## 5. Cambios que sí requieren desarrollo

La distribución de componentes, nuevas pantallas, reglas de avance, validaciones,
permisos o cálculos no son cambios estéticos. Esas modificaciones deben realizarse
en una fase funcional y probarse antes de publicarlas.

## Lista de comprobación visual

- Logo legible en fondo blanco.
- Contraste suficiente entre texto y fondo.
- Botones principales reconocibles.
- Campos y mensajes distinguibles sin depender sólo del color.
- Revisión en computadora y tableta.
- Ningún texto cortado con zoom del navegador al 125 %.
