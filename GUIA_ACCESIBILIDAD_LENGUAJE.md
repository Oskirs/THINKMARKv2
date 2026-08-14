# Paso 6.8.1 — Accesibilidad móvil y adecuación del lenguaje

## Propósito

Este ajuste prepara el MVP THINKMARK v2 para estudiantes de quinto y séptimo semestre
de distintas licenciaturas. Atiende dos riesgos observados en una prueba externa:

1. En algunos celulares con modo oscuro, los campos podían verse negros y ocultar el texto.
2. Algunas instrucciones utilizaban un lenguaje más cercano a posgrado que a licenciatura.

El objetivo no es reducir la exigencia del razonamiento. Se conserva la profundidad de la
actividad, pero las instrucciones se presentan con frases directas, preguntas concretas y
ayudas breves.

## Ajustes incorporados

### 1. Lectura y escritura en celular

- Fondo, texto, cursor, texto de ejemplo y estados deshabilitados tienen colores explícitos.
- La aplicación mantiene una interfaz clara aunque el dispositivo solicite modo oscuro.
- Los campos usan 16 px en celular para evitar el acercamiento automático de algunos navegadores.
- Las áreas de respuesta tienen una altura mínima de 118 px.
- Las acciones principales tienen un área táctil mínima de 48 px y ocupan el ancho disponible.
- Las columnas se apilan y las tarjetas reducen sus márgenes en pantallas de hasta 768 px.
- Las tablas permiten desplazamiento interno sin ensanchar toda la página.

### 2. Lenguaje claro para licenciatura

- Se cambiaron instrucciones largas por acciones observables: identificar, explicar, comparar,
  decidir y justificar.
- Las preguntas del recorrido usan expresiones cotidianas sin perder los cuatro componentes del
  Reasoning Delta: problema, evidencia, análisis crítico de IA y justificación de decisiones.
- Los mensajes técnicos de recuperación se sustituyeron por indicaciones comprensibles para el
  estudiante.
- Los conceptos indispensables se conservan y se explican dentro de la interfaz.

### 3. Glosario breve dentro del recorrido

La política versionada está en `config/language.json`. Incluye definiciones breves de:

- evidencia;
- supuesto;
- contraargumento;
- costo o renuncia de una decisión;
- incertidumbre;
- Reasoning Delta;
- ThinkMark.

La ayuda aparece sólo en las etapas donde el concepto es necesario, para no sobrecargar la
pantalla.

## Criterios de redacción para casos futuros

Cada caso adaptado por carrera y semestre deberá cumplir estas reglas:

1. Presentar una decisión reconocible para la disciplina.
2. Explicar siglas y conceptos la primera vez que aparecen.
3. Preferir oraciones cortas y una pregunta por instrucción.
4. Evitar palabras abstractas cuando exista una alternativa directa.
5. No confundir lenguaje claro con respuestas fáciles: la dificultad debe estar en analizar la
   evidencia y justificar la decisión.
6. Conservar las mismas cuatro dimensiones del Reasoning Delta para permitir comparación entre
   carreras.
7. Probar el texto con al menos un estudiante del semestre objetivo antes del piloto.

## Lista de verificación antes de publicar un caso

- [ ] El título y la decisión central pueden entenderse sin explicación del profesor.
- [ ] El caso distingue datos disponibles de información faltante.
- [ ] Las palabras técnicas necesarias tienen una explicación breve.
- [ ] Las preguntas no sugieren una respuesta correcta.
- [ ] El AI Coach pregunta, solicita evidencia y señala límites; no resuelve el caso.
- [ ] La primera respuesta y la reflexión final evalúan las mismas cuatro dimensiones.
- [ ] La vista fue probada en un celular real con modo claro y oscuro.
- [ ] Todo campo permite leer lo escrito, el cursor y el mensaje de ejemplo.
- [ ] No existe desplazamiento horizontal en las pantallas principales.
- [ ] Los botones principales se pueden pulsar cómodamente con una mano.

## Validación técnica de esta entrega

La pantalla E02 fue probada con una ventana de 390 × 844 px. El resultado comprobado fue:

- ancho del documento: 390 px, sin desplazamiento horizontal;
- campos de respuesta: fondo blanco y texto azul oscuro;
- cursor: color institucional vino;
- modo de color de los controles: claro;
- áreas de respuesta: 118 px de altura;
- botones principales: 48 px de altura y ancho completo.

Las pruebas automáticas verifican contraste mínimo, presencia del glosario, público objetivo,
reglas responsive y ausencia de expresiones avanzadas no explicadas en las pantallas del
estudiante.

## Alcance y siguiente ajuste

Este paso mejora la presentación y la comprensión del recorrido general. La selección de carrera
y semestre y la adaptación automática del caso se implementarán como un módulo separado, usando
esta política de lenguaje como requisito para todos los casos. Así se conserva la transversalidad
sin modificar la rúbrica común de THINKMARK.
