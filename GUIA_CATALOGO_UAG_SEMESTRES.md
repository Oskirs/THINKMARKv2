# Paso 6.8.3 — Catálogo UAG y adaptación por semestre

## Resultado

E01 utiliza un menú jerárquico:

1. Escuela o área académica.
2. Carrera o programa.
3. Semestre del piloto: 1.º, 5.º o 7.º.

El catálogo se basa en la oferta profesional presencial de Guadalajara publicada por la UAG y
consultada el 14 de agosto de 2026: `https://www.uag.mx/es/profesional`. Incluye 41 programas y
una opción transversal para una carrera todavía no configurada.

## Escuelas incluidas

- Escuela de Medicina y Ciencias de la Salud.
- UAG Business School.
- Escuela de Ingenierías y Agroindustria.
- Escuela de Arquitectura y Ambientes Construidos.
- Escuela de Derecho y Humanidades.
- Escuela de Industrias Creativas.
- Escuela de Ciencia de Datos e Inteligencia Artificial.

La oferta puede cambiar. El archivo `data/fixtures/academic_case_catalog.json` conserva la URL,
fecha de consulta, alcance de campus y nota de mantenimiento.

## Tres niveles del piloto

### 1.er semestre — Exploración introductoria

El estudiante reconoce actores, distingue un dato de una opinión y explica una decisión inicial
con una razón sencilla. Los conceptos técnicos deben explicarse antes de exigir su uso.

### 5.º semestre — Aplicación guiada

El estudiante delimita el problema, separa datos de supuestos y propone una decisión con una
salvaguarda explícita.

### 7.º semestre — Decisión con restricciones

El estudiante compara evidencia en tensión, anticipa efectos para distintos grupos y justifica
el costo o renuncia que acepta.

## Cómo se generan las variantes

No se mantienen 126 documentos independientes. Cada variante combina:

- un escenario específico de la carrera;
- dos hechos y una afirmación de verificación definidos por la escuela;
- un foco y una restricción definidos por el semestre;
- la misma rúbrica Reasoning Delta v2.

La combinación de 42 perfiles —41 carreras y la opción transversal— con tres semestres produce
126 variantes verificables. Al crear la sesión, la aplicación guarda una copia completa del caso;
una actualización posterior del catálogo no cambia el recorrido ya iniciado.

## ¿Conviene incorporar todos los semestres ahora?

La arquitectura ya permite añadir cualquier semestre desde el JSON, sin modificar E01 ni la lógica
de generación. Para el MVP no conviene publicar niveles que el equipo todavía no impartirá o no ha
validado. Esto aumentaría el contenido a revisar, haría más difícil el piloto y podría sugerir una
cobertura pedagógica que aún no existe.

La recomendación es mantener 1.º, 5.º y 7.º durante el piloto y añadir otros semestres cuando exista:

1. una materia concreta;
2. un resultado de aprendizaje definido;
3. un profesor responsable de revisar el nivel;
4. una prueba breve con estudiantes del semestre objetivo.

## Interpretación responsable

La misma rúbrica permite observar cambio dentro de cada recorrido, pero no debe utilizarse para
concluir que un semestre o una carrera “razona mejor” que otra. En el piloto, los resultados deben
analizarse por materia y cohorte antes de presentar agregados institucionales.

## Lista de verificación

- [ ] E01 filtra las carreras después de seleccionar la escuela.
- [ ] El menú ofrece 1.º, 5.º y 7.º semestre.
- [ ] E02 muestra el perfil y escenario correspondiente.
- [ ] Los conceptos de 1.er semestre usan explicación introductoria.
- [ ] El caso asignado permanece fijo al recuperar el código.
- [ ] El catálogo oficial se revisa antes de cada nuevo ciclo.
- [ ] Los resultados se interpretan por materia y cohorte.
