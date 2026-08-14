# Paso 6.8.2 — Selección de carrera, semestre y adaptación del caso

> Este documento conserva el diseño inicial. El catálogo oficial jerárquico y la variante de
> 1.er semestre se documentan en `GUIA_CATALOGO_UAG_SEMESTRES.md`.

## Resultado funcional

La pantalla E01 incorpora dos menús obligatorios antes del código de participante:

1. Carrera o programa académico.
2. Semestre del piloto: 5.º o 7.º.

La combinación seleccionada asigna un caso disciplinar y un nivel de análisis. La carrera,
el semestre, la versión del catálogo y una copia exacta del caso quedan guardados con la sesión.
Al recuperar el código, el estudiante conserva el mismo caso aunque el catálogo sea actualizado.

## Principio de transversalidad

La adaptación modifica únicamente el contexto del caso, los hechos disponibles, la pregunta
central y el nivel de complejidad. No modifica:

- las cuatro dimensiones del Reasoning Delta;
- la secuencia E01–E10;
- las reglas del AI Coach;
- la evaluación humana;
- el derecho del estudiante a corregir o no aprobar su ThinkMark.

Esto permite comparar el desarrollo del razonamiento con una estructura común, sin exigir que
estudiantes de carreras diferentes analicen un contexto ajeno a su formación.

## Catálogo piloto incluido

- Caso transversal / otra carrera.
- Administración y Negocios.
- Derecho.
- Ingeniería de Software y Sistemas.
- Mercadotecnia y Comunicación.
- Medicina y Ciencias de la Salud.
- Psicología.

El catálogo es demostrativo y no pretende representar la oferta académica oficial completa de la
UAG. Vive en `data/fixtures/academic_case_catalog.json`, por lo que puede ampliarse sin modificar
las pantallas ni la lógica del recorrido.

## Adaptación por semestre

### 5.º semestre — Aplicación guiada

El estudiante identifica el problema, separa datos de supuestos y propone una decisión con al
menos una salvaguarda. El caso ofrece una condición operativa concreta para orientar el análisis.

### 7.º semestre — Decisión con restricciones

El estudiante compara evidencia en tensión, anticipa efectos para distintos grupos y explica qué
costo aceptaría. El caso añade actores con interpretaciones distintas y una restricción de recursos.

La diferencia está en la complejidad del contexto, no en usar una rúbrica diferente.

## Trazabilidad y protección de la sesión

Cada registro conserva:

- `academic_profile`: carrera, área, semestre, nivel y versión del catálogo;
- `case_snapshot`: copia del caso asignado;
- `case_version`: versión aceptada junto con el consentimiento;
- `baseline_snapshot.case_id`: caso utilizado para la primera respuesta.

Una vez asignados, el repositorio impide modificar el perfil o el caso. Esto evita mezclar
respuestas de dos variantes y protege la interpretación del Reasoning Delta.

## Sesiones creadas antes de 6.8.2

Si una sesión anterior todavía no tiene una primera respuesta cerrada, el sistema le asigna el
perfil seleccionado al recuperarla. Si la primera respuesta ya fue cerrada, conserva el caso
transversal anterior y queda marcada como sesión de versión previa. Nunca se cambia un caso después
de haber sellado la línea base.

## Cómo agregar una carrera

1. Duplicar un elemento de `programs` en el catálogo JSON.
2. Crear un `program_id` único y estable.
3. Redactar título, contexto, pregunta central, tres hechos y afirmación para Verify.
4. Aplicar la lista de lenguaje claro de `GUIA_ACCESIBILIDAD_LENGUAJE.md`.
5. Probar ambas variantes de semestre con estudiantes o profesores del área.
6. Ejecutar las pruebas antes de publicar.

No deben agregarse respuestas modelo al texto visible del caso. El AI Coach debe seguir haciendo
preguntas y solicitando evidencia, sin resolver la decisión disciplinar.

## Verificación previa al piloto

- [ ] Los dos menús son visibles en E01 desde computadora y celular.
- [ ] No es posible continuar sin seleccionar carrera y semestre.
- [ ] E02 muestra la carrera, el semestre y el caso correspondiente.
- [ ] Cambiar de carrera produce una pregunta central disciplinar diferente.
- [ ] 5.º y 7.º añaden focos de análisis distintos.
- [ ] Recuperar un código mantiene el caso asignado originalmente.
- [ ] La cola del evaluador muestra el contexto académico de la sesión.
- [ ] La rúbrica aplicada sigue siendo Reasoning Delta v2 para todos los perfiles.
