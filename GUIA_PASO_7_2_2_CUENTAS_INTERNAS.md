# Paso 7.2.2 — Acceso por correo y cuentas internas

## Objetivo

Crear dos identidades internas distintas en Supabase Auth y asociarlas a los roles protegidos
de THINKMARK. Los estudiantes no se registran en Auth y continúan usando códigos pseudónimos.

## Decisión para el piloto

El MVP actual inicia sesión con correo y contraseña, pero todavía no procesa enlaces de
invitación o recuperación. Para evitar un enlace incompleto se crearán las cuentas desde el
Dashboard con contraseña robusta y correo confirmado. No usar **Send invitation** en este paso.

## 1. Restringir el registro público

En **Authentication → Sign In / Providers → Email**:

1. Mantener habilitado el proveedor Email.
2. Desactivar **Allow new users to sign up**.
3. Mantener deshabilitado el acceso anónimo.
4. Guardar los cambios.

Desactivar el registro impide que personas externas creen cuentas por su cuenta; las altas
administrativas desde el Dashboard siguen siendo el mecanismo autorizado del piloto.

## 2. Preparar las dos cuentas

Se requieren dos correos institucionales diferentes:

- Una cuenta para `evaluator`.
- Una cuenta para `teacher`.

No se debe reutilizar una sola cuenta para ambos roles. Cada contraseña debe ser única,
aleatoria, tener al menos 16 caracteres y almacenarse en un gestor de contraseñas.

## 3. Crear el evaluador

1. Abrir **Authentication → Users**.
2. Seleccionar **Add user → Create new user**.
3. Escribir el correo institucional del evaluador.
4. Pegar la contraseña aleatoria preparada para esa persona.
5. Activar **Auto Confirm User** o su opción equivalente.
6. Crear la cuenta.

## 4. Crear el profesor

Repetir el procedimiento con un correo y una contraseña diferentes. Confirmar que la lista
muestre dos usuarios y que ambos aparezcan con correo confirmado.

No escribir el rol en `user_metadata` o `raw_user_meta_data`; esos campos son editables y no
se utilizan para autorización en THINKMARK.

## 5. Asignar los roles protegidos

1. Abrir `supabase/onboarding/assign_internal_roles_template.sql`.
2. Copiarlo en una consulta nueva de SQL Editor.
3. Sustituir únicamente:
   - `EVALUADOR@INSTITUCION.EDU`
   - `PROFESOR@INSTITUCION.EDU`
4. Ejecutar la consulta.

La plantilla se detiene si falta una cuenta, si el correo coincide con más de un usuario o si
se intenta asignar ambos roles a la misma identidad.

## 6. Resultado esperado

La consulta final debe devolver dos filas:

| role | display_code | active | email_confirmed |
|---|---|---|---|
| evaluator | EV-PILOTO-01 | true | true |
| teacher | DOC-PILOTO-01 | true | true |

Los correos y contraseñas no deben aparecer en capturas, documentos del proyecto ni GitHub.

## Criterio de cierre

- El registro público está desactivado.
- Existen exactamente las dos cuentas internas previstas.
- Ambas tienen correo confirmado.
- `profiles` muestra un rol distinto para cada cuenta.
- No existen cuentas estudiantiles en Supabase Auth.

