# Paso 7.2.3 — Conectar Streamlit con Supabase mediante Secrets

## Objetivo

Cambiar la aplicación publicada del almacenamiento local de demostración a la persistencia
multiusuario de Supabase, sin colocar claves en GitHub ni en archivos públicos.

## Antes de comenzar

Tener disponibles en una nota bloqueada o gestor de contraseñas:

- URL HTTPS del proyecto Supabase.
- Clave `sb_publishable_...`.
- Clave `sb_secret_...` creada para `thinkmark-streamlit-pilot`.

No utilizar las claves heredadas `anon` o `service_role`.

## 1. Abrir los secretos de Streamlit

1. Abrir `https://thinkmarkv2.streamlit.app/`.
2. Seleccionar **Manage app**.
3. Abrir **Settings**.
4. Entrar a **Secrets**.

El editor puede mostrar valores sin ocultarlos. No tomar capturas, compartir pantalla ni pegar
su contenido en conversaciones.

## 2. Conservar secretos opcionales existentes

Si ya existen `OPENAI_API_KEY` u `OPENAI_MODEL`, conservar sus líneas exactamente como están.
No duplicar nombres. Los códigos `LOCAL_EVALUATOR_ACCESS_CODE` y
`LOCAL_TEACHER_ACCESS_CODE` ya no son necesarios en producción y pueden eliminarse.

## 3. Pegar la configuración

Agregar o sustituir las siguientes líneas con los valores reales:

```toml
PERSISTENCE_MODE = "supabase"
SUPABASE_URL = "https://TU-PROYECTO.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_REEMPLAZAR"
SUPABASE_SECRET_KEY = "sb_secret_REEMPLAZAR"
DEMO_INTERNAL_ACCESS = "false"
```

Reglas de formato:

- Mantener las comillas dobles.
- Una variable por línea.
- No agregar comas.
- No escribir espacios antes del prefijo de una clave.
- `SUPABASE_URL` es la URL del proyecto Supabase, no la URL de Streamlit.
- No pegar la contraseña de la base de datos ni las contraseñas de los usuarios.

## 4. Guardar y reiniciar

1. Seleccionar **Save**.
2. Esperar a que Streamlit procese la configuración.
3. Abrir **Manage app** nuevamente.
4. Seleccionar **Reboot app**.
5. Esperar a que la aplicación vuelva a estar disponible.

## 5. Verificación visible

1. Abrir la aplicación en una ventana privada.
2. Entrar al recorrido de estudiante.
3. Abrir la barra lateral.
4. Confirmar que muestra `Persistencia: Supabase`.

Después del cambio es normal que las sesiones locales anteriores no aparezcan: los archivos
efímeros de demostración no se migran a la nueva base. La prueba multiusuario debe comenzar con
un código nuevo.

## 6. Comprobación de accesos

En ventanas privadas separadas:

1. Iniciar sesión como evaluador con su correo y contraseña.
2. Cerrar la ventana.
3. Iniciar sesión como profesor con su cuenta distinta.
4. Confirmar que cada cuenta sólo abre su espacio autorizado.

No realizar todavía un recorrido estudiantil completo; esa prueba pertenece al paso 7.2.4.

## Errores esperables

- **Falta configuración obligatoria:** revisar que existan las tres variables de Supabase.
- **Configura una clave publishable vigente:** se pegó una clave heredada o incompleta.
- **Configura una clave secret vigente:** se pegó `service_role` o una clave incompleta.
- **DEMO_INTERNAL_ACCESS debe estar desactivado:** corregir el valor a `"false"`.
- **Conexión no disponible:** revisar la URL del proyecto y que las claves pertenezcan al mismo
  proyecto.

Ante un error, compartir sólo el mensaje de la aplicación o los logs que no contengan valores de
Secrets. Nunca compartir el editor de Secrets.

## Criterio de cierre

- La app inicia sin error de configuración.
- La barra lateral muestra `Persistencia: Supabase`.
- El acceso local de demostración está desactivado.
- Evaluador y profesor pueden autenticarse con sus cuentas y no intercambian roles.
- Ninguna clave fue subida a GitHub ni expuesta en una captura.

