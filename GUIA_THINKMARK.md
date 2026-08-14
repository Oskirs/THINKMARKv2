# Paso 6.6 — Human Reasoning Signature / ThinkMark

## Qué hace esta etapa

E09 convierte la evidencia ya registrada en una propuesta de nueve secciones. La
propuesta no es una evaluación: el estudiante la revisa y conserva la decisión final.

## Evidencia utilizada

- Posición inicial cerrada.
- Respuestas humanas al AI Coach.
- Verify, Challenge y Decide.
- Reflexión final enviada.
- Reasoning Delta validado por una persona.

No se envían códigos de participante ni datos de consentimiento al generador. El prompt
prohíbe añadir fuentes, decisiones, motivaciones, rasgos o logros que no estén expresados.

## Recorrido en E09

1. Presionar **Generar mi borrador de ThinkMark**.
2. Revisar las nueve secciones y editar cualquier texto que no represente el proceso.
3. Usar **Guardar cambios** para conservar correcciones sin tomar todavía una decisión.
4. Elegir una acción:
   - **Aprobar**: sólo funciona cuando el texto coincide con la propuesta generada.
   - **Corregir y aprobar**: exige al menos una modificación del estudiante.
   - **No aprobar**: registra la decisión y no crea una versión final.
   - **Rechazar esta propuesta y regenerar**: conserva la anterior y genera otra; el MVP
     permite hasta tres propuestas y exige explicar qué debe representar mejor.
5. Confirmar que se revisaron las nueve secciones.

Al aprobar, `thinkmark_final` guarda el texto exacto mostrado, fecha, tipo de aprobación
y sello SHA-256. Después de la decisión, los datos protegidos quedan en sólo lectura.

## Generación y alternativa local

La configuración vive en `config/thinkmark.json` y el contrato pedagógico en
`config/prompts/thinkmark_synthesis_v1.txt`. Si existe `OPENAI_API_KEY`, la integración
usa una salida estructurada. Si no existe clave, hay un error o la salida está incompleta,
una síntesis local mantiene funcional el recorrido y explicita los campos sin evidencia.

Se puede usar `OPENAI_THINKMARK_MODEL` para cambiar únicamente el modelo de esta etapa,
o `OPENAI_MODEL` como configuración común con el AI Coach.

## Prueba mínima recomendada

1. Recuperar una sesión con Reasoning Delta validado.
2. Generar una propuesta y guardar una corrección.
3. Regenerar una vez y comprobar que aparecen dos versiones en el historial.
4. Aprobar con correcciones.
5. Recargar la sesión y verificar que las nueve secciones estén bloqueadas y que el sello
   de integridad sea el mismo.
