# THINKMARK v2 — prototipo Streamlit

MVP para hacer visible el cambio del razonamiento humano antes, durante y después
de una interacción guiada con IA. El paso 6.4 incorpora un AI Coach socrático mediante
un adaptador de Responses API, guardrails y un banco pedagógico de fallo seguro. Todavía
no envía información a Supabase.

## Qué contiene

- 12 pantallas: E01–E10, V01 y D01.
- Navegación secuencial y estado temporal con `st.session_state`.
- E01 funcional con tres consentimientos obligatorios.
- E02 funcional con borrador recuperable, validaciones y cierre irreversible.
- E03 con hasta tres preguntas socráticas, salida estructurada, trazabilidad y cierre decidido por el estudiante.
- Adaptador OpenAI configurable y fallback que conserva el recorrido cuando no hay clave o la salida se bloquea.
- E04–E07 funcionales, secuenciales y recuperables.
- Envío final a estado `awaiting_review` sin sobrescribir la línea base.
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

## Configurar el AI Coach del paso 6.4

El prototipo funciona inmediatamente con el banco pedagógico seguro. Para activar la
API real, seguir `GUIA_AI_COACH.md`. Los secretos se leen desde `.streamlit/secrets.toml`
o variables de entorno y nunca deben entrar al repositorio.

La configuración desacoplada está en `config/ai_coach.json`. El modelo predeterminado
puede sobrescribirse con `OPENAI_MODEL` sin cambiar el código.

## Persistencia temporal

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
4. Para IA real, agregar `OPENAI_API_KEY` y opcionalmente `OPENAI_MODEL` en los secretos de la app.

El MVP utiliza únicamente componentes nativos de Streamlit en producción. Esta
decisión evita que la demostración falle por dependencias opcionales de gráficas.

La conexión a Supabase, las políticas de seguridad y el despliegue final corresponden
al paso 6.8.

## Límite del paso 6.4

El Coach sólo acompaña E03 y no busca fuentes ni evalúa el trabajo. V01 es únicamente
una vista previa: la evaluación y el Reasoning Delta se implementarán en el paso 6.5.
