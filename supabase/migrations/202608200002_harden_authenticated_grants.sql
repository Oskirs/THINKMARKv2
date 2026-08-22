-- THINKMARK v2 · Corrección de privilegios predeterminados de Supabase
-- Ejecutar una vez si la migración 202608130001 ya fue aplicada antes de esta corrección.

begin;

-- Retirar los privilegios amplios que Supabase puede conceder por defecto a las tablas
-- creadas en public. RLS continúa activo, pero se mantiene también el mínimo privilegio.
revoke all on public.profiles, public.thinkmark_sessions, public.session_assignments,
  public.learning_opportunities, public.access_audit from anon, authenticated;

-- El personal autenticado sólo puede leer su perfil, su asignación y los registros que
-- autoricen las políticas RLS. El profesor puede insertar la oportunidad autorizada.
grant select on public.profiles, public.thinkmark_sessions, public.session_assignments,
  public.learning_opportunities to authenticated;
grant insert on public.learning_opportunities to authenticated;

commit;

