# THINKMARK v2 — prototipo Streamlit

MVP para hacer visible el cambio del razonamiento humano antes, durante y después
de una interacción guiada con IA. El paso 6.8.1 añade contraste estable en celulares,
diseño responsive y lenguaje claro para estudiantes de licenciatura.

## Qué contiene

- 12 pantallas: E01–E10, V01 y D01.
- Navegación secuencial y estado temporal con `st.session_state`.
- E01 funcional con tres consentimientos obligatorios.
- E02 funcional con borrador recuperable, validaciones y cierre irreversible.
- E03 con hasta tres preguntas socráticas, salida estructurada, trazabilidad y cierre decidido por el estudiante.
- Adaptador OpenAI configurable y fallback que conserva el recorrido cuando no hay clave o la salida se bloquea.
- E04–E07 funcionales, secuenciales y recuperables.
- Envío final a estado `awaiting_review` sin sobrescribir la línea base.
- V01 funcional con evidencia inicial/final, niveles enteros 1–4, notas obligatorias y validación humana.
- E08 funcional con promedios, deltas por dimensión e interpretación responsable.
- E09 funcional con nueve secciones editables, vista final y decisión explícita del estudiante.
- Generación estructurada con integración OpenAI opcional y síntesis local segura sin clave.
- Hasta tres propuestas trazables; regenerar nunca sobrescribe versiones anteriores.
- Aprobación sin cambios, aprobación con correcciones o decisión de no aprobar.
- ThinkMark final inmutable, versionado y con sello de integridad.
- E10 funcional con cinco valoraciones, dos comentarios opcionales y cinco controles del facilitador.
- Cierre de una sola escritura con comprobaciones técnicas, fecha y sello de integridad.
- D01 funcional con métricas agregadas, fortaleza, oportunidad, evidencia e intervención.
- Propuesta docente mediante reglas auditables, editable y aceptable, ajustable o rechazable.
- Evaluación validada inmutable, versionada y con sello de integridad.
- Persistencia JSON local mediante un repositorio reemplazable por Supabase.
- Caso y recorrido de demostración separados del código.
- Dashboard docente con gráfica nativa y oportunidad de aprendizaje.
- Configuración estética desacoplada.
- Paleta alineada con los colores observados en los activos públicos oficiales de la UAG.
- Pruebas automáticas para el registro de pantallas y los fixtures.
- Portal de acceso separado para estudiante, evaluador/facilitador y profesor.
- Cola de revisión limitada a las sesiones asignadas a cada evaluador.
- Repositorios intercambiables: JSON local para demostración y Supabase para publicación.
- Migración SQL con RLS, roles protegidos, auditoría y control de concurrencia.
- Configuración de producción que se detiene si faltan secretos, sin volver al modo local.
- Campos con fondo, texto, cursor y estados de lectura definidos para modo claro u oscuro.
- Columnas y acciones que se acomodan verticalmente en pantallas de celular.
- Política versionada de lenguaje claro y glosario breve dentro del recorrido estudiantil.
- Guía de accesibilidad y redacción para validar nuevos casos antes de publicarlos.
- Menús jerárquicos de escuela, carrera y semestre en E01.
- Catálogo presencial UAG Guadalajara con 42 programas, una opción transversal y 129 variantes para 1.º, 5.º y 7.º.
- Caso y nivel de complejidad fijados con la sesión para conservar trazabilidad al reingresar.

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

## Persistencia y modos de operación

El ajuste 7.3.1 añade sesiones grupales con código `TM-XXXXXX`, vínculo explícito de cada
recorrido y selección del evaluador por sesión y participante. La operación y migración están
documentadas en `GUIA_PASO_7_3_1_SESIONES.md`.

Los ajustes 7.3.2 a 7.3.5 incorporan contadores preventivos, conservación de borradores,
preguntas conceptualmente delimitadas, menos respuestas abiertas e indicadores agregados de
posible fatiga. Se documentan en `GUIA_AJUSTES_7_3_2_A_7_3_5.md`.

Las sesiones se guardan en `data/runtime/sessions.json`; la carpeta está excluida de
Git cuando `PERSISTENCE_MODE = "local"`. Este modo sirve para una demostración controlada,
pero no para un piloto real porque el almacenamiento de Streamlit Community Cloud es efímero.

Para trabajo multiusuario se usa `PERSISTENCE_MODE = "supabase"`. La aplicación exige URL,
clave publicable y clave secreta válidas; las sesiones, asignaciones y oportunidades se
guardan en Supabase. La configuración completa está en `GUIA_SUPABASE_DESPLIEGUE.md`.

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

## Publicación multiusuario

1. Crear Supabase y ejecutar `supabase/migrations/202608130001_thinkmark_v2.sql`.
2. Crear las cuentas internas y asignar los expedientes a sus evaluadores.
3. Subir esta carpeta a un repositorio privado de GitHub.
4. Crear la app en Streamlit Community Cloud seleccionando `app.py`.
5. Agregar los secretos de Supabase y, si se usará IA real, los de OpenAI.
6. Verificar el recorrido completo en tres ventanas privadas, una por rol.

El MVP utiliza únicamente componentes nativos de Streamlit en producción. Esta
decisión evita que la demostración falle por dependencias opcionales de gráficas.

No subir `.streamlit/secrets.toml`. La guía incluye las comprobaciones previas al piloto.

## Evaluación y Reasoning Delta del paso 6.5

La configuración aprobada de la rúbrica vive en `config/reasoning_delta_rubric.json`.
El evaluador aplica los mismos cuatro criterios al momento inicial y final; la aplicación
no asigna niveles. Sólo valida completitud, calcula `final - inicial` y publica una evaluación
que ya fue confirmada por una persona.

Reasoning Delta es evidencia formativa descriptiva. No debe interpretarse como inteligencia,
diagnóstico, calificación, cambio obligatorio de opinión ni efecto causal probado.

## Human Reasoning Signature del paso 6.6

La configuración está en `config/thinkmark.json` y las instrucciones de uso y prueba en
`GUIA_THINKMARK.md`. La aplicación sólo entrega una propuesta construida con evidencia del
recorrido. El texto final pertenece al estudiante: puede editar, regenerar, aprobar o decidir
no aprobar. Únicamente una aprobación explícita crea `thinkmark_final`.

## Feedback, cierre y dashboard del paso 6.7

Las instrucciones de operación están en `GUIA_CIERRE_DASHBOARD.md`. El feedback del
estudiante y los controles del facilitador están separados. El dashboard no ordena ni
diagnostica personas: agrega únicamente sesiones autorizadas y Deltas previamente validados
por una persona. La oportunidad es una propuesta hasta que el profesor la acepta, ajusta o rechaza.

## Supabase y separación de accesos del paso 6.8

La guía operativa está en `GUIA_SUPABASE_DESPLIEGUE.md` y el ejemplo de secretos en
`.streamlit/secrets.toml.example`. El estudiante entra con un código privado; evaluador y
profesor usan correo, contraseña y rol protegido. V01 y los controles de cierre pertenecen
al evaluador/facilitador; D01 pertenece al profesor.

El código, la migración y las pruebas están listos. Crear el proyecto externo, emitir
credenciales y publicar la URL requiere una cuenta autorizada del equipo.

## Accesibilidad móvil y lenguaje claro del paso 6.8.1

La implementación y la lista de verificación están documentadas en
`GUIA_ACCESIBILIDAD_LENGUAJE.md`. Los controles mantienen contraste explícito, los campos usan
16 px en celular, las acciones se apilan y el vocabulario esencial se explica en el momento en
que se utiliza. La dificultad permanece en el análisis, no en descifrar las instrucciones.

## Catálogo UAG y adaptación por semestre del paso 6.8.3

La implementación está documentada en `GUIA_CATALOGO_UAG_SEMESTRES.md`. E01 exige seleccionar
escuela, carrera y semestre antes de crear la sesión; E02 muestra el contexto asignado. Las
variantes de 1.º, 5.º y 7.º cambian la complejidad del caso, pero conservan las mismas cuatro
dimensiones de Reasoning Delta para todos los perfiles. `GUIA_TRANSVERSALIDAD_CASOS.md` conserva
el antecedente funcional del paso 6.8.2.
