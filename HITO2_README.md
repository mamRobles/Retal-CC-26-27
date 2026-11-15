# Hito 2
## ¿Cómo ejecutar la aplicación?
Primero creamos nuestras claves env y después hacemos un docker compose up:
`$ cp .env.example .env && docker compose up --build`
## Cómo funcionan los docker de postgres
Postgres arranca como root y su entrypoint es el que se encarga de bajar al usuario postgres sin acceso root.
## Justificaciones de las imágenes docker utilizadas
¿Por qué utilizar python:3.13-slim en vez de -alpine? Precisamente porque alpine usa musl en vez de glibc, esto hace que muchos wheels (incluido el de postgre utilizado en esta práctica) se rompan completamente.

¿Por qué slim y no base? Porque base tiene muchos paquetes que no nos interesan basados en Debian que no son necesarios para instalar nuestra aplicación.

db_retales/db_materiales son la imagen de postgre, que ya tiene el usuario postgre por defecto con el mínimo privilegio.
## Cómo es el compose
Tiene 4 contenedores, dos bases de datos y dos microservicios, y 3 redes. Las redes son entre las bases de datos y sus servicios y entre los servicios. Tienen healthchecks programados como un get /health de los servicios.

Los volúmenes tienen nombres representativos de lo que hacen (materiales, db_materiales...).

## CI (integración continua)
Para este propósito se redacta un yml con diferentes actions metidas en un solo archivo.
### ¿Cuándo se activan los actions?
Cuando hacemos push o pull request a main se activan. No queremos usarlos en develop necesariamente porque gastaría los créditos limitados de integración continua que puedan tener las plataformas que usamos.
### ruff
Ruff es un linter de python, revisa el código y se asegura de que está correctamente formateado. Es una dependencia de requirements-dev. Se revisa automáticamente.
### hadolint
Hadolint es un linter, pero esta vez de dockerfiles. Se le indica en un mesh los 4 dockerfiles del proyecto y se le pide que los revise.
### Test unitarios
Son los tests definidos en los dos microservicios de la aplicación (retales_proyecto y materiales)
### Pruebas de integración
Esta vez creamos un compose con nuestro compose.yaml real, no uno falso para probar los servicios. Cuando lo lanzamos hacemos curl a las direcciones donde se lanzan los compose y comprobamos también las redes internas en los servicios.
### GHCR
Como queremos publicar correctamente nuestros contenedores de servicio a github, tenemos que subirlos (esos solo, no las bases de datos por dios) al github container registry. Esta action los sube automáticamente. Esta acción solo se hace en push, no en pull request, que sino los subimos sin saber si están bien.
