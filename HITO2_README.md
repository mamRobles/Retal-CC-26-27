# Hito 2
## Justificaciones de las imágenes docker utilizadas
¿Por qué utilizar python:3.13-slim en vez de -alpine? Precisamente porque alpine usa musl en vez de glibc, esto hace que muchos wheels (incluido el de postgre utilizado en esta práctica) se rompan completamente.

¿Por qué slim y no base? Porque base tiene muchos paquetes que no nos interesan basados en Debian que no son necesarios para instalar nuestra aplicación.

db_retales/db_materiales son la imagen de postgre, que ya tiene el usuario postgre por defecto con el mínimo privilegio.
## Cómo es el compose
Tiene 4 contenedores, dos bases de datos y dos microservicios, y 3 redes. Las redes son entre las bases de datos y sus servicios y entre los servicios. Tienen healthchecks programados como un get /health de los servicios.

Los volúmenes tienen nombres representativos de lo que hacen (materiales, db_materiales...).

## CI (integración continua)