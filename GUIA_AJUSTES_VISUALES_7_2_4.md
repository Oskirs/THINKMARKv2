# THINKMARK v2 — Ajustes visuales posteriores a Supabase

## Objetivo

Alinear la interfaz con el estado real del piloto y separar visualmente el contexto de estudiantes, evaluadores y profesores, sin modificar la autenticación, las políticas de acceso ni la estructura de datos de Supabase.

## Ajustes incorporados

1. **Estado dinámico del prototipo**
   - Con `PERSISTENCE_MODE="supabase"` el encabezado muestra **PILOTO CONTROLADO**.
   - Con `PERSISTENCE_MODE="local"` conserva **MODO DEMOSTRACIÓN**.

2. **Panel del profesor**
   - El título se presenta como **Dashboard docente de aprendizaje**.
   - Se elimina del menú lateral el bloque de “Sesión actual” y los avisos propios del recorrido estudiantil.
   - Se conservan el rol, la persistencia, el cierre de sesión y la navegación docente.

3. **Cola del evaluador**
   - En Supabase se informa que cada evaluador sólo puede consultar las sesiones que le fueron asignadas.
   - El aviso de sesiones de prueba se muestra únicamente en modo local.

4. **Pie de página**
   - En Supabase identifica la publicación como **Piloto controlado THINKMARK v2**.
   - En local conserva la referencia de prototipo.

## Archivos que deben sustituirse

- `app.py`
- `src/ui/brand.py`
- `src/ui/layout.py`
- `src/screens/access.py`
- `src/screens/faculty.py`

El archivo de pruebas incluido es opcional para Streamlit Cloud:

- `tests/test_mobile_accessibility_language.py`

## Publicación

1. Descomprime el paquete.
2. Sustituye los archivos anteriores respetando exactamente sus carpetas.
3. Guarda los cambios en GitHub.
4. Espera el despliegue automático de Streamlit Cloud o usa **Manage app → Reboot app**.
5. Abre la aplicación en una ventana privada para evitar mostrar una sesión anterior almacenada por el navegador.

## Resultado esperado

- La portada conectada a Supabase muestra **PILOTO CONTROLADO**.
- La vista del profesor no presenta código de sesión ni instrucciones de E01.
- El dashboard docente aparece completamente en español.
- La cola del evaluador muestra un mensaje consistente con Supabase.

## Verificación técnica

Se ejecutaron 49 pruebas automatizadas y todas finalizaron correctamente.
