# Paso 6.7 — Feedback, cierre y oportunidad docente

## E10 · Feedback y cierre

E10 se habilita después de que el estudiante toma una decisión explícita sobre su
ThinkMark, tanto si la aprueba como si decide no aprobarla.

### Bloque del estudiante

Registra cinco valoraciones de 1 a 5:

1. Utilidad del AI Coach.
2. Utilidad de Verify.
3. Agencia sobre la decisión final.
4. Fidelidad del ThinkMark.
5. Intención de reutilizar la actividad.

También puede responder, de forma opcional, qué fue útil y qué resultó confuso o
repetitivo. El feedback se envía una sola vez y no modifica Reasoning Delta ni ThinkMark.

### Bloque del facilitador

El facilitador usa un código pseudónimo y confirma cinco controles:

1. Recorrido completado sin asistencia técnica relevante.
2. Evidencia registrada y valorada.
3. AI Coach no resolutivo.
4. Cuatro dimensiones comparables.
5. ThinkMark revisada y con decisión explícita.

Puede documentar incidencias técnicas, sin incluir juicios personales. Al cerrar, la
aplicación ejecuta además cinco comprobaciones técnicas, guarda fecha y sello SHA-256 y
bloquea el feedback contra sobrescritura.

## D01 · Faculty Learning Dashboard

La vista inicial es agregada y muestra:

- sesiones iniciadas, completas y con Delta validado;
- tasa de finalización y mediana de duración disponible;
- Delta medio por dimensión;
- promedio agregado de las cinco valoraciones de experiencia;
- fortaleza, oportunidad, evidencia e intervención sugerida.

La propuesta se obtiene mediante reglas auditables. Se prioriza la dimensión con menor
nivel final medio y, en caso de empate, menor cambio medio. No se utiliza IA ni se crean
perfiles, diagnósticos o rankings.

## Validación docente

El profesor debe:

1. Revisar la fortaleza, oportunidad, evidencia e intervención.
2. Elegir **Aceptar sin cambios**, **Validar con ajustes** o **Rechazar**.
3. Si ajusta, modificar al menos una pieza; si rechaza, explicar la razón.
4. Confirmar que la decisión fue tomada por una persona.

La propuesta original y la versión final se guardan por separado. La decisión docente es
de una sola escritura y conserva fecha y sello de integridad.

## Restricción vigente

E10 y D01 identifican claramente los bloques de estudiante, facilitador y profesor, pero
todavía no autentican roles. Deben utilizarse sólo en una prueba controlada. El paso 6.8
añadirá Supabase y separación real de accesos.
