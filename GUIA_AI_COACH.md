# Configuración del AI Coach — paso 6.4

El Coach puede operar en dos modos sin cambiar la interfaz:

- **IA conectada:** usa OpenAI Responses API y una salida estructurada.
- **Banco pedagógico seguro:** se activa cuando no hay clave, la API falla o una salida no supera los guardrails.

En ambos modos el estudiante puede terminar el recorrido. La aplicación nunca solicita ni muestra la clave en pantalla.

## Activar OpenAI en desarrollo local

1. Instalar las dependencias de `requirements.txt`.
2. Copiar `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml`.
3. Sustituir el valor de ejemplo por una clave de proyecto válida.
4. Reiniciar Streamlit.

El archivo `.streamlit/secrets.toml` está excluido por `.gitignore`. No debe enviarse por correo, incluirse en un ZIP ni subirse a GitHub.

## Activar OpenAI en Streamlit Community Cloud

1. Abrir la aplicación en Streamlit Community Cloud.
2. Entrar a **Manage app → Settings → Secrets**.
3. Agregar:

```toml
OPENAI_API_KEY = "clave-del-proyecto"
OPENAI_MODEL = "gpt-5.4-mini"
```

4. Guardar y reiniciar la aplicación.

## Configuración sin tocar las pantallas

El archivo `config/ai_coach.json` controla proveedor, modelo, versiones de política y prompt, máximo de turnos, timeout y fallback. El prompt versionado está en `config/prompts/coach_socratic_v1.txt`. `OPENAI_MODEL` puede sobrescribir el modelo desde secretos o variables de entorno.

## Guardrails implementados

- Una sola pregunta por turno.
- Longitud acotada.
- Sin listas de soluciones, recomendación directa ni texto entregable.
- Foco limitado a las cuatro dimensiones de Reasoning Delta.
- Salida estructurada y validación posterior independiente.
- Máximo de tres preguntas por sesión.
- Respuesta humana guardada antes de solicitar la siguiente pregunta.
- Fallback automático y trazable.
- Contexto minimizado: caso, una dimensión de la línea base y hasta dos turnos anteriores.

## Evidencia técnica guardada

Cada turno conserva pregunta visible, respuesta del estudiante, foco, modo, modelo, versiones, latencia, tokens reportados y activación de seguridad. No se guarda la clave, el prompt interno ni razonamiento oculto del modelo.

Antes de un piloto con estudiantes reales, el responsable institucional debe revisar privacidad, tratamiento de datos, presupuesto, modelo autorizado y términos vigentes del proveedor.
