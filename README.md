# THINKMARK v2 — prototipo Streamlit

MVP para hacer visible el cambio del razonamiento humano antes, durante y después
de una interacción guiada con IA. El paso 6.2 incorpora acceso pseudónimo, consentimiento,
recuperación de sesión y línea base inmutable. Todavía no envía información a Supabase
ni a una API de IA.

## Qué contiene

- 12 pantallas: E01–E10, V01 y D01.
- Navegación secuencial y estado temporal con `st.session_state`.
- E01 funcional con tres consentimientos obligatorios.
- E02 funcional con borrador recuperable, validaciones y cierre irreversible.
- Persistencia JSON local mediante un repositorio reemplazable por Supabase.
- Caso y recorrido de demostración separados del código.
- Dashboard docente con gráfica nativa y oportunidad de aprendizaje.
- Configuración estética desacoplada.
- Paleta alineada con los colores observados en los activos públicos oficiales de la UAG.
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

## Persistencia temporal del paso 6.2

Las sesiones se guardan en `data/runtime/sessions.json`; la carpeta está excluida de
Git. Esto permite probar recuperación e inmutabilidad sin configurar servicios externos.
En Streamlit Community Cloud el almacenamiento local es efímero y no debe usarse para
un piloto real. El paso 6.8 reemplazará este adaptador por Supabase con políticas de acceso.

## Pruebas

```bash
pytest -q
python -m compileall app.py src tests
```

Las herramientas de prueba están separadas en `requirements-dev.txt` para evitar
instalarlas en Streamlit Community Cloud. Para desarrollo puede usarse:

```bash
python -m pip install -r requirements-dev.txt
```

## Publicación preliminar

1. Subir esta carpeta a un repositorio de GitHub.
2. En Streamlit Community Cloud, crear una app desde el repositorio.
3. Seleccionar `app.py` como archivo principal.
4. No agregar secretos todavía: el paso 6.1 no los necesita.

El MVP utiliza únicamente componentes nativos de Streamlit en producción. Esta
decisión evita que la demostración falle por dependencias opcionales de gráficas.

La conexión a Supabase, las políticas de seguridad y el despliegue final corresponden
al paso 6.8. La IA real se incorpora en el paso 6.4 mediante un adaptador separado.

## Límite del paso 6.2

E03 y las pantallas posteriores permanecen bloqueadas hasta cerrar la línea base.
Después del cierre se habilitan como vistas demostrativas; su lógica se incorporará
en los pasos 6.3–6.7.
