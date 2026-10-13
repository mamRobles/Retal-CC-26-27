# Retal
Proyecto de desarrollo Cloud para la asignatura Cloud Computing de una aplicación de gestión personal de materiales y patrones para la realización de proyectos de arte textil.
## Herramientas utilizadas
Python 
Django
Tailwind css
git
VScodium
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
TODO: Diagrama formal detallando componentes, protocolos de comunicación entre microservicios y almacenamiento.
## Especificación de API REST
TODO: Documentación sintética de los endpoints principales (rutas, verbos HTTP, payloads JSON).
