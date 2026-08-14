# Paso 6.8 — Supabase, accesos separados y publicación multiusuario

Una publicación compartida debe usar `PERSISTENCE_MODE = "supabase"`. El modo local se
conserva únicamente para demostración sin infraestructura.

## 1. Decisiones institucionales previas

Definir responsable del proyecto, región de alojamiento, plazo de conservación,
procedimiento de eliminación, responsables de cuentas y protocolo ante exposición de una
clave. THINKMARK no debe recibir nombres, matrículas, correos estudiantiles, biometría ni
datos de navegación; el correo se reserva para cuentas internas.

## 2. Crear Supabase

1. Crear un proyecto.
2. En **Settings → API Keys**, obtener una clave `sb_publishable_...` y una
   `sb_secret_...`. No usar las claves heredadas en nuevas configuraciones.
3. No guardar la clave secret en código, GitHub, URLs, documentos ni capturas.
4. Ejecutar en **SQL Editor**:
   `supabase/migrations/202608130001_thinkmark_v2.sql`.
5. Revisar **Security Advisor** y confirmar que las cinco tablas tienen RLS.

La migración crea perfiles, sesiones, asignaciones, oportunidades, auditoría y una función
de guardado atómico disponible únicamente para el backend.

## 3. Crear cuentas internas

Crear o invitar usuarios en **Authentication → Users** y registrar su rol desde SQL Editor:

```sql
insert into public.profiles (id, role, display_code)
select id, 'evaluator', 'EV-PILOTO-01'
from auth.users where email = 'evaluador@institucion.edu';

insert into public.profiles (id, role, display_code)
select id, 'teacher', 'DOC-PILOTO-01'
from auth.users where email = 'profesor@institucion.edu';
```

Nunca usar `raw_user_meta_data` para autorización. La aplicación verifica la contraseña y
vuelve a comprobar el rol protegido en `profiles`.

## 4. Asignar sesiones al evaluador

Después de que el estudiante envía Reflect:

```sql
insert into public.session_assignments (session_id, user_id, assignment_role)
select s.session_id, u.id, 'evaluator'
from public.thinkmark_sessions s
cross join auth.users u
where s.participant_code = 'TM-CODIGO-ASIGNADO'
  and u.email = 'evaluador@institucion.edu'
on conflict do nothing;
```

La cola mostrará únicamente sesiones asignadas en modo Supabase.

## 5. Configurar secretos

Usar `.streamlit/secrets.toml.example` como referencia:

```toml
PERSISTENCE_MODE = "supabase"
SUPABASE_URL = "https://TU-PROYECTO.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_..."
SUPABASE_SECRET_KEY = "sb_secret_..."
DEMO_INTERNAL_ACCESS = "false"
```

Si falta una variable, la app se detiene; no cambia silenciosamente a JSON local.

## 6. Verificar antes de publicar

```bash
python scripts/verify_configuration.py
pytest -q
streamlit run app.py
```

Probar con tres ventanas privadas:

1. **Estudiante:** completa, consulta Delta, decide ThinkMark y envía feedback.
2. **Evaluador/facilitador:** abre sólo una sesión asignada, valida la rúbrica y después
   realiza los controles de cierre.
3. **Profesor:** ve agregados y acepta, ajusta o rechaza la oportunidad.

Comprobar que un código estudiantil no abre V01 ni D01.

## 7. Publicar en Streamlit Community Cloud

1. Subir el proyecto a un repositorio privado de GitHub.
2. Crear la aplicación usando `app.py`.
3. En **Advanced settings → Secrets**, pegar las variables anteriores.
4. Confirmar la instalación de `requirements.txt`.
5. Repetir la prueba de tres roles en la URL publicada.

`secrets.toml` está excluido de Git y nunca debe subirse.

## 8. Antes del piloto

- Revisar usuarios, asignaciones, logs y Security Advisor.
- Cambiar inmediatamente cualquier clave expuesta.
- Definir limpieza de sesiones de prueba y retención.
- Usar códigos de participante aleatorios y distribuirlos privadamente.
- Probar exportación anonimizada y recuperación ante incidentes.

## Límite de esta entrega

El código, migración, RLS, autenticación y configuración están listos. Crear el proyecto,
las cuentas, las claves y la publicación requiere al propietario autorizado del equipo.
