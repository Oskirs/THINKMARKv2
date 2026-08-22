-- Paso 7.3.1 · Verificación de sólo lectura.

select table_name
from information_schema.tables
where table_schema = 'public'
  and table_name in ('activity_sessions', 'activity_session_assignments');

select column_name, is_nullable, data_type
from information_schema.columns
where table_schema = 'public'
  and table_name = 'thinkmark_sessions'
  and column_name = 'activity_session_id';

select session_code, status
from public.activity_sessions
where session_code = 'TM-LEGACY';

select count(*) as recorridos_sin_sesion_grupal
from public.thinkmark_sessions
where activity_session_id is null;

select tablename, policyname
from pg_policies
where schemaname = 'public'
  and tablename in ('activity_sessions', 'activity_session_assignments')
order by tablename, policyname;

select routine_name
from information_schema.routines
where routine_schema = 'public'
  and routine_name = 'save_thinkmark_session_v2';
