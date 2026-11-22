# Hito 2
## ¿Cómo ejecutar la aplicación?
Primero creamos nuestras claves env y después hacemos un docker compose up:
`$ cp .env.example .env && docker compose up --build`
Si se desea crear un up **como producción** (sin herramientas de desarrollo, arrancando el servidor con gunicorn y desactivando DEBUG) hay que ejecutar:
`$ cp .env.example .env &&  docker compose -f compose.yaml up --build`
En .env hay que añadir las claves secretas, las credenciales de las bases de datos y el SERVICE_TOKEN. Si falta alguna el compose **NO ARRANCA**.
## ¿Dónde se lanza?
La aplicación se abre en `http://localhost:8000`, la api de los materiales está en `localhost:8001`.
## Dockerfiles y compose
### Cómo funcionan los docker de postgres
Postgres arranca como root y su entrypoint es el que se encarga de bajar al usuario postgres sin acceso root.
### Justificaciones de las imágenes docker utilizadas
¿Por qué utilizar python:3.13-slim en vez de -alpine? Precisamente porque alpine usa musl en vez de glibc, esto hace que muchos wheels (incluido el de postgre utilizado en esta práctica) se rompan completamente.

¿Por qué slim y no base? Porque base tiene muchos paquetes que no nos interesan basados en Debian que no son necesarios para instalar nuestra aplicación.

db_retales/db_materiales son la imagen de postgre, que ya tiene el usuario postgre por defecto con el mínimo privilegio.
### Cómo es el compose
Tiene 4 contenedores, dos bases de datos y dos microservicios, y 3 redes. Las redes son entre las bases de datos y sus servicios y entre los servicios. Tienen healthchecks programados como un get /health de los servicios.

Los volúmenes tienen nombres representativos de lo que hacen (materiales, db_materiales...).
### Multi-stage
retales y materiales tienen un usuario al que cambian no root antes de arrancar.
#### Multi-stage en retales
- css instala las dependencias de build y compila tailwind
- dev parte de css y añade herramientas de desarrollo (el código se monta desde el disco, solo la usa compose.override.yaml)
- final instala requirements y recibe de css el styles css compilado.
#### Multi-stage en materiales
builder crea un venv en /opt/venv e instala las dependencias y luego runtime solo copia /opt/venv para no tener nada de pip ni lo que se usa para instalar.
### Requisitos de la práctica
Tenemos 4 contenedores con 3 redes aisladas que los comunican. Los puertos son separados para retales y materiales. Tenemos volúmenes persistentes retales_db_data y materiales_db_data montados en /var/lib/postgresql/data. Solo se borran si se añade -v.
#### Healthchecks
Para comprobar el health se revisa pg_isready en las bases de datos y los servicios tienen un GET a /health.
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
## Decisiones de diseño
Se separa materiales como un solo microservicio. Se querría separar más cosas como microservicios pero por las decisiones de diseño el alcance se ha hecho mayor que las capacidades y se ha mantenido un servicio monolítico web.
Si se borra un usuario, sus materiales se quedan huérfanos en el microservicio, esto se considera un posible error o limitación conocida.
Para pedir grosor y fibras como listas para creación de un material, se hace un request a /api/choices en vez de copiarlos en retales para asegurar persistencia.
Si materiales cae, Retales sigue funcionando, pero manda 504 en caso de que mandes un formulario a materiales.
Las respuestas de error son explícitas y claras, usando códigos HTTP propios de cada caso.
Se descarta el panel de admin (HU6) por restricciones de tiempo para favorecer otras funcionalidades más importantes.