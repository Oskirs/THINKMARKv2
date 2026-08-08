# THINKMARK v2 — prototipo Streamlit

Base navegable del MVP para hacer visible el cambio del razonamiento humano antes,
durante y después de una interacción guiada con IA. El paso 6.1 utiliza exclusivamente
datos simulados: todavía no envía información a una base de datos ni a una API de IA.

## Qué contiene

- 12 pantallas: E01–E10, V01 y D01.
- Navegación y estado temporal con `st.session_state`.
- Caso y recorrido de demostración separados del código.
- Dashboard docente con oportunidad de aprendizaje.
- Configuración estética desacoplada.
- Pruebas automáticas para el registro de pantallas y los fixtures.

## Ejecutar localmente

Requiere Python 3.12. Desde esta carpeta:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Abrir `http://localhost:8501`. Para detener la aplicación, presionar `Control + C`.

## Personalizar logo, colores y tipografía sin tocar la lógica

La identidad visual vive fuera del código de negocio:

- `assets/`: logo e imágenes. Para sustituir el logo, copiar el archivo y actualizar
  `logo_path` en `config/brand.json`.
- `config/brand.json`: nombre, lema, paleta, tipografía y ruta del logo.
- `.streamlit/config.toml`: colores nativos de controles y fondos de Streamlit.
- `GUIA_PERSONALIZACION.md`: instrucciones y límites detallados para el equipo de diseño.

Los cambios estéticos no requieren modificar `app.py`, servicios, navegación ni datos.
Conviene mantener suficiente contraste y probar la vista en computadora y tableta.

## Cambiar el caso de demostración

Editar o duplicar `data/fixtures/demo_case.json`. El cargador valida campos mínimos y
mantiene el contenido independiente de las pantallas.

## Pruebas

```bash
pytest -q
python -m compileall app.py src tests
```

## Publicación preliminar

1. Subir esta carpeta a un repositorio de GitHub.
2. En Streamlit Community Cloud, crear una app desde el repositorio.
3. Seleccionar `app.py` como archivo principal.
4. No agregar secretos todavía: el paso 6.1 no los necesita.

La conexión a Supabase, las políticas de seguridad y el despliegue final corresponden
al paso 6.8. La IA real se incorpora en el paso 6.4 mediante un adaptador separado.

## Límite del paso 6.1

Las doce rutas están abiertas intencionalmente para revisión del equipo. El bloqueo
secuencial, la línea base inmutable y la recuperación de sesión se implementarán en
el paso 6.2.
