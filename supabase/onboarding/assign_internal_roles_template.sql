-- THINKMARK v2 · Asignación controlada de roles internos
-- Reemplazar sólo los dos correos. No incluir contraseñas en esta consulta.

begin;

do $$
declare
  v_evaluator_email text := 'EVALUADOR@INSTITUCION.EDU';
  v_teacher_email text := 'PROFESOR@INSTITUCION.EDU';
  v_evaluator_id uuid;
  v_teacher_id uuid;
  v_match_count integer;
begin
  if v_evaluator_email = 'EVALUADOR@INSTITUCION.EDU'
     or v_teacher_email = 'PROFESOR@INSTITUCION.EDU' then
    raise exception 'Reemplaza los dos correos de ejemplo antes de ejecutar.';
  end if;

  select count(*)
  into v_match_count
  from auth.users
  where lower(email) = lower(v_evaluator_email);

  if v_match_count <> 1 then
    raise exception 'La cuenta de evaluador debe existir exactamente una vez en Authentication.';
  end if;

  select id
  into v_evaluator_id
  from auth.users
  where lower(email) = lower(v_evaluator_email);

  select count(*)
  into v_match_count
  from auth.users
  where lower(email) = lower(v_teacher_email);

  if v_match_count <> 1 then
    raise exception 'La cuenta de profesor debe existir exactamente una vez en Authentication.';
  end if;

  select id
  into v_teacher_id
  from auth.users
  where lower(email) = lower(v_teacher_email);

  if v_evaluator_id = v_teacher_id then
    raise exception 'Evaluador y profesor deben utilizar cuentas diferentes.';
  end if;

  insert into public.profiles (id, role, display_code, active)
  values (v_evaluator_id, 'evaluator'::public.app_role, 'EV-PILOTO-01', true)
  on conflict (id) do update
  set role = excluded.role,
      display_code = excluded.display_code,
      active = true;

  insert into public.profiles (id, role, display_code, active)
  values (v_teacher_id, 'teacher'::public.app_role, 'DOC-PILOTO-01', true)
  on conflict (id) do update
  set role = excluded.role,
      display_code = excluded.display_code,
      active = true;
end
$$;

commit;

-- Debe devolver dos filas sin mostrar correos ni identificadores internos.
select
  p.role,
  p.display_code,
  p.active,
  (u.email_confirmed_at is not null) as email_confirmed
from public.profiles p
join auth.users u on u.id = p.id
where p.display_code in ('EV-PILOTO-01', 'DOC-PILOTO-01')
order by p.role;
