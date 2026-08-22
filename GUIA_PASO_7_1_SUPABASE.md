# Paso 7.1 — Creación y configuración de Supabase

## Objetivo

Crear la base de datos multiusuario de THINKMARK, instalar su estructura de seguridad y
dejar preparadas las credenciales que se configurarán en Streamlit durante el paso 7.2.
Este paso no modifica las pantallas ni el recorrido pedagógico.

## Resultado esperado

Al terminar deben existir:

- Un proyecto de Supabase propiedad del equipo autorizado.
- Cinco tablas con Row Level Security (RLS) activado.
- Dos funciones de base de datos.
- Los roles internos `evaluator`, `teacher` y `admin`.
- Una clave publicable y una clave secreta específica para el backend de Streamlit.
- Ningún nombre, matrícula, correo estudiantil o clave guardada en GitHub.

## Antes de crear el proyecto

Definir y registrar:

1. Responsable institucional de la cuenta y un segundo administrador de respaldo.
2. Región de alojamiento aprobada por la institución.
3. Plazo de conservación de las sesiones del piloto.
4. Procedimiento para borrar pruebas y atender una clave expuesta.
5. Gestor de contraseñas donde se conservarán la contraseña de la base de datos y las claves.

Para el piloto, THINKMARK usa códigos pseudónimos. No se deben cargar nombres, matrículas,
correos estudiantiles, biometría ni datos clínicos reales.

## 1. Crear el proyecto

1. Entrar a `https://supabase.com/dashboard` con la cuenta institucional autorizada.
2. Crear o seleccionar la organización del equipo.
3. Elegir **New project**.
4. Nombre sugerido: `thinkmark-piloto-uag`.
5. Generar una contraseña robusta para la base de datos y guardarla en el gestor de
   contraseñas. No enviarla por chat o correo.
6. Elegir la región aprobada por la institución y cercana a los usuarios del piloto.
7. Crear el proyecto y esperar a que su estado sea saludable.

## 2. Ejecutar la migración THINKMARK

1. En el proyecto abrir **SQL Editor**.
2. Crear una consulta nueva.
3. Abrir el archivo:
   `supabase/migrations/202608130001_thinkmark_v2.sql`.
4. Copiar todo su contenido en el editor.
5. Revisar que el proyecto seleccionado sea `thinkmark-piloto-uag`.
6. Ejecutar una sola vez. La migración es repetible para sus objetos principales, pero no
   debe usarse como sustituto de un control formal de versiones.

La migración crea:

- `profiles`: rol autorizado del personal interno.
- `thinkmark_sessions`: recorrido pseudónimo del estudiante.
- `session_assignments`: expedientes asignados al evaluador.
- `learning_opportunities`: oportunidad de aprendizaje revisada por el profesor.
- `access_audit`: registro de acciones internas relevantes.
- `current_app_role()`: consulta segura del rol interno.
- `save_thinkmark_session(...)`: guardado atómico con control de concurrencia.

## 3. Verificar la instalación

1. Crear otra consulta en **SQL Editor**.
2. Ejecutar el archivo:
   `supabase/verification/202608200001_verify_thinkmark_v2.sql`.
3. Confirmar lo siguiente:

   - Aparecen cinco tablas y todas muestran `rowsecurity = true`.
   - Aparecen cinco políticas RLS.
   - Aparecen las dos funciones de THINKMARK.
   - El enum `app_role` contiene `evaluator`, `teacher` y `admin`.
   - No aparece ninguna concesión de tabla para el rol `anon`.
   - Para `authenticated` aparecen sólo cinco filas: cuatro permisos `SELECT` y un
     permiso `INSERT` sobre `learning_opportunities`.

4. Abrir **Security Advisor** y revisar cada advertencia. No marcar una advertencia como
   resuelta sin comprender su efecto.

## 4. Obtener las credenciales de aplicación

En **Project Settings → API Keys**:

1. Copiar la URL HTTPS del proyecto.
2. Crear o identificar una clave **Publishable** con prefijo `sb_publishable_`.
3. Crear una clave **Secret** con prefijo `sb_secret_`, con nombre sugerido
   `thinkmark-streamlit-pilot`.
4. Guardarlas en el gestor de contraseñas.

La clave publishable se utilizará para autenticar al evaluador y al profesor. La clave
secret es de servidor, omite RLS y sólo debe colocarse en los secretos protegidos de
Streamlit. Nunca debe pegarse en GitHub, capturas, documentos, URLs o esta conversación.

## 5. Información que se usará en el siguiente paso

Sin enviar sus valores por chat, tener disponibles:

```toml
PERSISTENCE_MODE = "supabase"
SUPABASE_URL = "https://...supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_..."
SUPABASE_SECRET_KEY = "sb_secret_..."
DEMO_INTERNAL_ACCESS = "false"
```

Estos valores se pegarán directamente en **Streamlit Community Cloud → App settings →
Secrets** durante el paso 7.2.

## Criterio de cierre del paso 7.1

El paso queda terminado cuando:

- La consulta de verificación devuelve la estructura esperada.
- RLS está activo en las cinco tablas.
- `authenticated` no conserva permisos `DELETE`, `TRUNCATE`, `TRIGGER`, `REFERENCES` ni
  `UPDATE` sobre las tablas del piloto.
- Security Advisor no presenta hallazgos críticos sin resolver.
- Las claves están resguardadas y no aparecen en el repositorio.
- Todavía no se han cargado estudiantes ni información personal.

## Fuentes técnicas

- Claves de Supabase: https://supabase.com/docs/guides/getting-started/api-keys
- Row Level Security: https://supabase.com/docs/guides/database/postgres/row-level-security
- Seguridad de datos: https://supabase.com/docs/guides/database/secure-data
