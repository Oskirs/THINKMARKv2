# Paso 7.3.1 — Sesiones y trazabilidad

## Flujo operativo

1. El profesor entra al dashboard y crea una sesión.
2. THINKMARK genera un código compartido con formato `TM-XXXXXX`.
3. El profesor asigna un evaluador y comparte el código con el grupo.
4. Cada estudiante ingresa el código de sesión y su código anónimo individual.
5. Las respuestas guardan `activity_session_id`, `session_code`, `session_id` y `participant_id`.
6. El evaluador selecciona primero la sesión y después al participante.

## Estados

- `open`: acepta participantes nuevos y permite continuar avances existentes.
- `closed`: no acepta participantes nuevos; quienes ya ingresaron pueden terminar.
- `archived`: queda disponible sólo para consulta interna.

## Aplicación en Supabase

1. Respaldar el proyecto y revisar que las migraciones anteriores estén aplicadas.
2. Ejecutar `supabase/migrations/202608210001_sessions_traceability.sql`.
3. Ejecutar `supabase/verification/202608210002_verify_sessions_traceability.sql`.
4. Confirmar que `recorridos_sin_sesion_grupal` sea cero.
5. Publicar esta versión de la app después de aplicar la migración.

La migración conserva registros anteriores en la sesión cerrada `TM-LEGACY`. No modifica
respuestas selladas, evaluaciones validadas ni hashes existentes.

Si una sesión se creó sin evaluador, asignarlo desde SQL Editor:

```sql
insert into public.activity_session_assignments (activity_session_id, user_id)
select s.activity_session_id, p.id
from public.activity_sessions s
cross join public.profiles p
where s.session_code = 'TM-XXXXXX'
  and p.display_code = 'EV-PILOTO-01'
  and p.role = 'evaluator'
on conflict do nothing;
```

## Comprobación del piloto

- Crear una sesión, copiar el código y abrir el acceso estudiantil en otra ventana.
- Intentar un código inexistente y confirmar que no crea respuestas.
- Cerrar la sesión y confirmar que un participante nuevo no puede entrar.
- Confirmar que un participante ya registrado sí puede recuperar su avance.
- Ingresar como evaluador y revisar la ruta sesión → participante → respuestas.
