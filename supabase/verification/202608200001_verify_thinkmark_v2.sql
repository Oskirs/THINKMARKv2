-- THINKMARK v2 · Verificación de instalación del paso 7.1
-- Sólo realiza consultas de lectura. Ejecutar desde Supabase SQL Editor.

-- 1. Deben aparecer cinco tablas y rowsecurity debe ser true en todas.
select
  schemaname,
  tablename,
  rowsecurity
from pg_catalog.pg_tables
where schemaname = 'public'
  and tablename in (
    'profiles',
    'thinkmark_sessions',
    'session_assignments',
    'learning_opportunities',
    'access_audit'
  )
order by tablename;

-- 2. Deben aparecer cinco políticas RLS de THINKMARK.
select
  schemaname,
  tablename,
  policyname,
  cmd,
  roles
from pg_catalog.pg_policies
where schemaname = 'public'
  and tablename in (
    'profiles',
    'thinkmark_sessions',
    'session_assignments',
    'learning_opportunities',
    'access_audit'
  )
order by tablename, policyname;

-- 3. Deben aparecer current_app_role y save_thinkmark_session.
select
  routine_schema,
  routine_name,
  routine_type,
  security_type
from information_schema.routines
where routine_schema = 'public'
  and routine_name in ('current_app_role', 'save_thinkmark_session')
order by routine_name;

-- 4. Deben aparecer evaluator, teacher y admin.
select
  t.typname as enum_name,
  e.enumlabel as enum_value
from pg_catalog.pg_type t
join pg_catalog.pg_enum e on e.enumtypid = t.oid
join pg_catalog.pg_namespace n on n.oid = t.typnamespace
where n.nspname = 'public'
  and t.typname = 'app_role'
order by e.enumsortorder;

-- 5. No debe aparecer ninguna fila cuyo grantee sea anon.
-- Deben aparecer exactamente cinco filas de authenticated:
-- SELECT en profiles, thinkmark_sessions, session_assignments y learning_opportunities;
-- INSERT en learning_opportunities.
select
  grantee,
  table_name,
  privilege_type
from information_schema.role_table_grants
where table_schema = 'public'
  and table_name in (
    'profiles',
    'thinkmark_sessions',
    'session_assignments',
    'learning_opportunities',
    'access_audit'
  )
  and grantee in ('anon', 'authenticated')
order by grantee, table_name, privilege_type;
