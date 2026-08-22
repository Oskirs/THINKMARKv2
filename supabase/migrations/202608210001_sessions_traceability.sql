-- THINKMARK v2 · Paso 7.3.1 · Sesiones grupales y trazabilidad
-- Migración incremental: ejecutar después de 202608200002_harden_authenticated_grants.sql.

create table if not exists public.activity_sessions (
  activity_session_id uuid primary key default gen_random_uuid(),
  session_code text not null unique,
  title text not null,
  activity_id text not null default 'CASO-DEMO-01-v1',
  status text not null default 'open',
  created_by uuid references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  closed_at timestamptz,
  archived_at timestamptz,
  constraint activity_sessions_code_format check (session_code ~ '^TM-[A-Z0-9]{6}$'),
  constraint activity_sessions_title_length check (char_length(trim(title)) between 3 and 120),
  constraint activity_sessions_status check (status in ('open', 'closed', 'archived'))
);

create table if not exists public.activity_session_assignments (
  activity_session_id uuid not null references public.activity_sessions(activity_session_id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  assignment_role public.app_role not null default 'evaluator'
    check (assignment_role = 'evaluator'),
  assigned_at timestamptz not null default now(),
  primary key (activity_session_id, user_id)
);

alter table public.thinkmark_sessions
  add column if not exists activity_session_id uuid
  references public.activity_sessions(activity_session_id);

-- Los registros previos se conservan dentro de una sesión cerrada de compatibilidad.
insert into public.activity_sessions (session_code, title, status)
values ('TM-LEGACY', 'Sesiones anteriores al ajuste 7.3.1', 'closed')
on conflict (session_code) do nothing;

update public.thinkmark_sessions
set activity_session_id = (
  select activity_session_id from public.activity_sessions where session_code = 'TM-LEGACY'
)
where activity_session_id is null;

create index if not exists idx_activity_sessions_status
  on public.activity_sessions(status);
create index if not exists idx_activity_sessions_creator
  on public.activity_sessions(created_by);
create index if not exists idx_activity_session_assignments_user
  on public.activity_session_assignments(user_id);
create index if not exists idx_thinkmark_sessions_activity_session
  on public.thinkmark_sessions(activity_session_id);

create or replace function public.save_thinkmark_session_v2(
  p_activity_session_id uuid,
  p_participant_code text,
  p_session_id text,
  p_record jsonb,
  p_expected_revision bigint
)
returns bigint
language plpgsql
security definer
set search_path = public
as $$
declare
  current_revision bigint;
  current_activity_session_id uuid;
  activity_status text;
  next_revision bigint;
begin
  select status into activity_status
  from public.activity_sessions
  where activity_session_id = p_activity_session_id;

  if activity_status is null then
    raise exception 'activity_session_not_found';
  end if;

  select revision, activity_session_id
  into current_revision, current_activity_session_id
  from public.thinkmark_sessions
  where participant_code = p_participant_code
  for update;

  if current_revision is null then
    if activity_status <> 'open' then
      raise exception 'activity_session_not_open';
    end if;
    if p_expected_revision <> 0 then
      raise exception 'revision_conflict';
    end if;
    insert into public.thinkmark_sessions(
      session_id, participant_code, activity_session_id, activity_id,
      record, session_status, completed, revision
    ) values (
      p_session_id,
      p_participant_code,
      p_activity_session_id,
      coalesce(p_record->'consent_record'->>'case_version', 'CASO-DEMO-01-v1'),
      p_record,
      coalesce(p_record->>'session_status', 'in_progress'),
      coalesce((p_record->>'completed')::boolean, false),
      1
    );
    return 1;
  end if;

  if current_activity_session_id <> p_activity_session_id then
    raise exception 'participant_code_already_used';
  end if;
  if activity_status = 'archived' then
    raise exception 'activity_session_archived';
  end if;
  if current_revision <> p_expected_revision then
    raise exception 'revision_conflict';
  end if;

  next_revision := current_revision + 1;
  update public.thinkmark_sessions
  set record = p_record,
      session_status = coalesce(p_record->>'session_status', session_status),
      completed = coalesce((p_record->>'completed')::boolean, false),
      revision = next_revision,
      updated_at = now()
  where participant_code = p_participant_code
    and activity_session_id = p_activity_session_id;
  return next_revision;
end;
$$;

revoke all on function public.save_thinkmark_session_v2(uuid, text, text, jsonb, bigint)
  from public, anon, authenticated;
grant execute on function public.save_thinkmark_session_v2(uuid, text, text, jsonb, bigint)
  to service_role;

alter table public.activity_sessions enable row level security;
alter table public.activity_session_assignments enable row level security;

drop policy if exists "teacher_own_activity_sessions_read" on public.activity_sessions;
create policy "teacher_own_activity_sessions_read" on public.activity_sessions
for select to authenticated
using (
  (public.current_app_role() in ('teacher', 'admin') and created_by = (select auth.uid()))
  or exists (
    select 1 from public.activity_session_assignments a
    where a.activity_session_id = activity_sessions.activity_session_id
      and a.user_id = (select auth.uid())
      and a.assignment_role = 'evaluator'
  )
);

drop policy if exists "teacher_activity_sessions_insert" on public.activity_sessions;
create policy "teacher_activity_sessions_insert" on public.activity_sessions
for insert to authenticated
with check (
  public.current_app_role() in ('teacher', 'admin')
  and created_by = (select auth.uid())
);

drop policy if exists "teacher_own_activity_sessions_update" on public.activity_sessions;
create policy "teacher_own_activity_sessions_update" on public.activity_sessions
for update to authenticated
using (
  public.current_app_role() in ('teacher', 'admin')
  and created_by = (select auth.uid())
)
with check (
  public.current_app_role() in ('teacher', 'admin')
  and created_by = (select auth.uid())
);

drop policy if exists "activity_assignment_member_read" on public.activity_session_assignments;
create policy "activity_assignment_member_read" on public.activity_session_assignments
for select to authenticated
using (
  user_id = (select auth.uid())
  or exists (
    select 1 from public.activity_sessions s
    where s.activity_session_id = activity_session_assignments.activity_session_id
      and s.created_by = (select auth.uid())
      and public.current_app_role() in ('teacher', 'admin')
  )
);

drop policy if exists "teacher_activity_assignment_insert" on public.activity_session_assignments;
create policy "teacher_activity_assignment_insert" on public.activity_session_assignments
for insert to authenticated
with check (
  exists (
    select 1 from public.activity_sessions s
    where s.activity_session_id = activity_session_assignments.activity_session_id
      and s.created_by = (select auth.uid())
      and public.current_app_role() in ('teacher', 'admin')
  )
);

revoke all on public.activity_sessions, public.activity_session_assignments
  from anon, authenticated;
grant select, insert, update on public.activity_sessions to authenticated;
grant select, insert on public.activity_session_assignments to authenticated;
grant all on public.activity_sessions, public.activity_session_assignments to service_role;

comment on table public.activity_sessions is
  'Sesión grupal identificada por TM-XXXXXX; agrupa participantes sin reemplazar su código anónimo individual.';
comment on column public.thinkmark_sessions.activity_session_id is
  'Vínculo explícito entre el recorrido individual y la sesión grupal del ajuste 7.3.1.';
