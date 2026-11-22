# Retal
[Documentación del Hito 2](HITO2_README.md)

Proyecto de desarrollo Cloud para la asignatura Cloud Computing de una aplicación de gestión personal de materiales y patrones para la realización de proyectos de arte textil.
## Herramientas utilizadas
- `Python `
- `Docker`
- `Docker Compose`
- `Django`
- `Gunicorn`
- `WhiteNoise`
- `ruff`
- `hadolint`
- `Tailwind css`
- `PostgreSQL`
- `git y Github`
- `VScodium`
## Estrategia de ramas
- `main`: Rama protegida de cambios, solo se puede hacer pull request.
- `{feature}`: Las ramas de funcionalidades tendrán lo que añaden en su título (Ej. login, gestionMateriales, etc.).
### Commits semánticos
| Tipo | significado |
| -----|-------------|
| feat | Agrega nuevas características (feat: autenticación) |
| fix  | Corrección de errores (fix: corregido admin.py) |
| docs | Agregar o cambiar documentación (docs: sección nueva en README.md) |
| style | Correcciones menores de estilo o erratas (style: cambiada posición del botón de login) |
## Descripción del dominio
Esta aplicación pretender ser un *hub* en la nube para proyectos de arte textil. La ventaja de desplegar la solución en la nube es la capacidad de extender o reducir el almacenamiento de los materiales y los proyectos a medida que se crean. Además, en estos contextos es usual que la demanda varíe según eventos periódicos, puesto que es más común tejer jerseys en invierno que en verano y existen KAL (Knit Along) que ocupan meses específicos donde más usuarios accederán a la plataforma y la utilizarán.
### Casos de uso principales
-  Seguimiento de proyectos, progreso, materiales utilizados, opinión del proyecto al terminarlo, anotaciones importantes...
- Ver patrones que has guardado en la plataforma desde cualquier cliente en cualquier situación.
- Revisar materiales en cualquier lugar para saber qué falta y qué tienes.
## Justificación NIST SP 800-145
A continuación se van a analizar las cinco características esenciales del Cloud aplicadas al proyecto de Retales.
### Autoservicio bajo demanda
Un usuario debe ser capaz de almacenar todos los materiales que necesite en cualquier momento sin depender de la actuación de un administrador. Casos en los que esta propiedad es útil:
#### Acabo de entrar en la plataforma y quiero meter todo mi almacén de lana en el sistema
Retales debería poder adaptarse a la cantidad de recursos de almacenamiento que necesites sin requerir interacción adicional del administrador.
#### He decidido que ya no quiero la mitad de mis patrones en la plataforma y los voy a borrar
Retales liberará el espacio automáticamente sin carga adicional para el administrador ni para el usuario.
### Acceso amplio a la red
Esta es una de las propiedades más importantes de la plataforma. Permite realizar proyectos en cualquier parte, lo cual es crítico para artistas textiles. Ya sea que necesitas consultar un patrón en el autobús, necesitas ver tus reservas de hilo en la mercería o acabas de encontrar un evento y quieres registrar el proyecto; Retales debería funcionar desde cualquier lugar en cualquier momento.
### Agrupación (o asignación común) de recursos
No es necesario que los usuarios tengan recursos particulares asignados a ellos, ese concepto se abstrae y se vuelve una cuestión propia del administrador de la plataforma. Al poder compartir los recursos y asignarlos según sea necesario, la gestión del almacenamiento de los materiales de los usuarios se vuelve natural e intuitiva.
### Rápida elasticidad
Esta propiedad es siempre importante, pero es crítica cuando trata de eventos como Love Yarn Madrid, KAL, CAL, patrones populares como "Sophie scarf" y otros momentos en los que miles de personas van a estar modificando sus proyectos y añadiendo materiales a sus almacenas simultaneamente. La plataforma debe ser capaz tanto de gestionar épocas de baja actividad como eventos masivos.
### Servicio medido
La monitorización del servicio sirve para la gestión del sitio en eventos particulares y tomar medidas (crear colas, preventivamente contratar más ancho de banda) cuando ocurran.
## Mapeo de Actores NIST SP 500-292
En esta sección se van a identificar los roles principales del sistema:
- Consumidor: Artistas textiles que quieren hacer proyectos y tener sus almacenes en la plataforma.
- Proveedor: Yo soy la proveedora del servicio, pero también soy la consumidora de plataformas Cloud donde desplegaré el proyecto.
- Intermediario: No hay.
- Auditor: Como en esta asignatura vamos a desarrollar nada más el servicio, no tenemos auditor. Pero podríamos considerar a la profesora como auditora de evaluación de mi servicio.
- Operador: Será el proveedor de servicios de telecomunicación por el cual se comunique el usuario con el sistema. En España, el más prevalente es Telefónica.
### Impacto económico
Para sostenerse, la plataforma contará con monetización mediante anuncios. Estos anuncios pueden ser publicados por los propios usuarios (para vender un patrón o materiales) o por empresas que quisieran publicitar en la plataforma. Con este dinero se costeará el servicio en cloud de almacenamiento y ejecución.
## Diagrama de Arquitectura
<img width="1138" height="779" alt="diagramaCC" src="https://github.com/user-attachments/assets/53bac855-c562-4eb0-a2d7-8743e4af7518" />

## Especificación de la API
Modificado en HITO 2:
El sistema expone dos interfaces distintas:

1. **Rutas web de Retales**: páginas HTML renderizadas en el servidor (Django + plantillas).
   Al ser formularios HTML, solo usan `GET` (mostrar) y `POST` (enviar).
2. **API REST interna del microservicio `materiales`**: JSON sobre HTTP, solo accesible desde
   Retales dentro de la red `services_net`. No usa DRF: son vistas Django que devuelven `JsonResponse`.

### Rutas web de Retales

| Verbo | Ruta | Propósito | Acceso |
|---|---|---|---|
| GET | `/` | Portada | Público |
| GET | `/health/` | Healthcheck (lo usa Docker) | Público |
| GET, POST | `/registro/` | Crear cuenta | Público |
| GET, POST | `/cuenta/login/` | Iniciar sesión | Público |
| POST | `/cuenta/logout/` | Cerrar sesión | Logueado |
| GET | `/buscar/?q=&tecnica=&estado=&page=` | Búsqueda global de proyectos públicos con filtros | Público |
| GET | `/{usuario}/` | Perfil | Público |
| GET | `/{usuario}/proyectos/` | Proyectos del usuario (el dueño ve también los privados) | Público |
| GET, POST | `/{usuario}/proyectos/agregar/` | Crear proyecto | Dueño |
| GET | `/{usuario}/proyectos/{id}/` | Detalle del proyecto y sus materiales | Público si es público |
| GET, POST | `/{usuario}/proyectos/{id}/edit/` | Editar proyecto y enlazar materiales | Dueño |
| GET, POST | `/{usuario}/proyectos/{id}/delete/` | Confirmar y borrar proyecto | Dueño |
| GET | `/{usuario}/materiales/` | Materiales del usuario | Público |
| GET, POST | `/{usuario}/materiales/agregar/` | Crear material | Dueño |
| GET, POST | `/{usuario}/materiales/{id}/editar/` | Editar material | Dueño |
| GET, POST | `/{usuario}/materiales/{id}/borrar/` | Confirmar y borrar material | Dueño |
| GET | `/admin/` | Panel de administración (usuarios y proyectos) | Staff |

Si un usuario intenta modificar algo que no es suyo, recibe `404` (no se revela que existe).

### API REST del microservicio `materiales`

Autenticación entre servicios: cabecera `X-Service-Token` (comparada en tiempo constante).
Sin token válido → `401`. Método no permitido → `405`.
El contrato JSON usa claves en inglés (`title`, `yarn_weight`, `composition`…).

| Verbo | Ruta | Propósito | Respuestas |
|---|---|---|---|
| GET | `/health/` | Healthcheck (sin token) | `200` |
| GET | `/api/items/?created_by={usuario}` | Lista materiales (máx. 100), opcionalmente de un usuario | `200` |
| POST | `/api/items/` | Crea un material con su composición | `201`, `400` |
| GET | `/api/items/{id}/` | Un material | `200`, `404` |
| PUT | `/api/items/{id}/` | Reemplaza un material y su composición (`created_by` no se puede cambiar) | `200`, `400`, `404` |
| DELETE | `/api/items/{id}/` | Borra un material (la composición se borra en cascada) | `204`, `404` |
| GET | `/api/choices/` | Valores válidos de grosor de lana y fibras | `200` |

Los errores `400` devuelven `{"error": {campo: [mensajes]}}`, que Retales muestra en el campo
correspondiente del formulario.