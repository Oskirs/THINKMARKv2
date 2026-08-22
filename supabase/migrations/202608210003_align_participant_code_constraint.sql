-- THINKMARK v2 · Hotfix 7.4.2 · Formato de código anónimo
-- Alinea Supabase con src/domain/baseline.py: 6 a 20 caracteres,
-- letras, números o guion, sin exigir el prefijo reservado TM-.

begin;

alter table public.thinkmark_sessions
  drop constraint if exists thinkmark_sessions_participant_code_check;

alter table public.thinkmark_sessions
  add constraint thinkmark_sessions_participant_code_check
  check (participant_code ~ '^[A-Z0-9][A-Z0-9-]{5,19}$') not valid;

alter table public.thinkmark_sessions
  validate constraint thinkmark_sessions_participant_code_check;

commit;
