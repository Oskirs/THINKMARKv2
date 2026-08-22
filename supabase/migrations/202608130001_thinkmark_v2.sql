-- THINKMARK v2 · Persistencia multiusuario y separación de accesos
-- Ejecutar en Supabase SQL Editor con una cuenta administradora.

create extension if not exists pgcrypto;

do $$ begin
  create type public.app_role as enum ('evaluator', 'teacher', 'admin');
exception when duplicate_object then null;
end $$;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  role public.app_role not null,
  display_code text not null check (char_length(display_code) between 4 and 30),
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.thinkmark_sessions (
  session_id text primary key,
  participant_code text not null unique,
  activity_id text not null default 'CASO-DEMO-01-v1',
  record jsonb not null,
  session_status text not null default 'in_progress',
  completed boolean not null default false,
  revision bigint not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (participant_code ~ '^TM-[A-Z0-9-]{3,17}$')
);

create table if not exists public.session_assignments (
  session_id text not null references public.thinkmark_sessions(session_id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  assignment_role public.app_role not null check (assignment_role = 'evaluator'),
  assigned_at timestamptz not null default now(),
  primary key (session_id, user_id)
);

create table if not exists public.learning_opportunities (
  activity_id text primary key,
  record jsonb not null,
  teacher_id uuid references auth.users(id),
  created_at timestamptz not null default now()
);

create table if not exists public.access_audit (
  audit_id bigint generated always as identity primary key,
  actor_id uuid references auth.users(id),
  actor_role text not null,
  action text not null,
  target_type text not null,
  target_id text,
  created_at timestamptz not null default now()
);

create index if not exists idx_sessions_status on public.thinkmark_sessions(session_status);
create index if not exists idx_sessions_activity on public.thinkmark_sessions(activity_id);
create index if not exists idx_assignments_user on public.session_assignments(user_id);

create or replace function public.current_app_role()
returns public.app_role
language sql
stable
security definer
set search_path = public
as $$
  select role from public.profiles
  where id = (select auth.uid()) and active = true
$$;

revoke all on function public.current_app_role() from public, anon;
grant execute on function public.current_app_role() to authenticated, service_role;

create or replace function public.save_thinkmark_session(
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
  next_revision bigint;
begin
  select revision into current_revision
  from public.thinkmark_sessions
  where participant_code = p_participant_code
  for update;

  if current_revision is null then
    if p_expected_revision <> 0 then
      raise exception 'revision_conflict';
    end if;
    insert into public.thinkmark_sessions(
      session_id, participant_code, activity_id, record, session_status, completed, revision
    ) values (
      p_session_id,
      p_participant_code,
      coalesce(p_record->'consent_record'->>'case_version', 'CASO-DEMO-01-v1'),
      p_record,
      coalesce(p_record->>'session_status', 'in_progress'),
      coalesce((p_record->>'completed')::boolean, false),
      1
    );
    return 1;
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
  where participant_code = p_participant_code;
  return next_revision;
end;
$$;

revoke all on function public.save_thinkmark_session(text, text, jsonb, bigint) from public, anon, authenticated;
grant execute on function public.save_thinkmark_session(text, text, jsonb, bigint) to service_role;

alter table public.profiles enable row level security;
alter table public.thinkmark_sessions enable row level security;
alter table public.session_assignments enable row level security;
alter table public.learning_opportunities enable row level security;
alter table public.access_audit enable row level security;

drop policy if exists "profile_self_read" on public.profiles;
create policy "profile_self_read" on public.profiles
for select to authenticated
using ((select auth.uid()) = id);

drop policy if exists "evaluator_assigned_session_read" on public.thinkmark_sessions;
create policy "evaluator_assigned_session_read" on public.thinkmark_sessions
for select to authenticated
using (
  public.current_app_role() = 'evaluator'
  and exists (
    select 1 from public.session_assignments a
    where a.session_id = thinkmark_sessions.session_id
      and a.user_id = (select auth.uid())
      and a.assignment_role = 'evaluator'
  )
);

drop policy if exists "assignment_self_read" on public.session_assignments;
create policy "assignment_self_read" on public.session_assignments
for select to authenticated
using ((select auth.uid()) = user_id and public.current_app_role() = 'evaluator');

drop policy if exists "teacher_opportunity_read" on public.learning_opportunities;
create policy "teacher_opportunity_read" on public.learning_opportunities
for select to authenticated
using (public.current_app_role() in ('teacher', 'admin'));

drop policy if exists "teacher_opportunity_insert" on public.learning_opportunities;
create policy "teacher_opportunity_insert" on public.learning_opportunities
for insert to authenticated
with check (
  public.current_app_role() in ('teacher', 'admin')
  and teacher_id = (select auth.uid())
);

-- Supabase puede aplicar privilegios predeterminados a anon y authenticated al crear
-- tablas en public. Retirarlos de ambos roles antes de conceder sólo lo necesario.
revoke all on public.profiles, public.thinkmark_sessions, public.session_assignments,
  public.learning_opportunities, public.access_audit from anon, authenticated;
grant select on public.profiles, public.thinkmark_sessions, public.session_assignments,
  public.learning_opportunities to authenticated;
grant insert on public.learning_opportunities to authenticated;
grant all on public.profiles, public.thinkmark_sessions, public.session_assignments,
  public.learning_opportunities, public.access_audit to service_role;

comment on table public.thinkmark_sessions is
  'Registro JSONB transicional del MVP 6.8. Los artefactos sellados conservan hashes y se normalizarán después del piloto.';
comment on table public.profiles is
  'Roles internos controlados por administración; no usar raw_user_meta_data para autorización.';
