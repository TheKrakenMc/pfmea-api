# Matriz de permisos

La autorización se resuelve en el servidor. La selección de planta se valida contra asignaciones persistidas. Administrator tiene acceso global explícito, con una planta activa por solicitud.

| Actor | Lectura | Escritura | Equipos y aprobación |
|---|---|---|---|
| Administrator | Plantas existentes | Global; respeta revisión e inmutabilidad | Sí |
| PFMEA Owner | Proyectos asignados y plantas autorizadas | Documentos asignados y catálogos permitidos | Sólo proyectos que posee o donde figura como Owner |
| Team Member | Proyectos asignados y planta autorizada | Proyectos asignados, salvo membresía Viewer | No |
| Viewer | Recursos autorizados por planta y proyecto | No | No |
| Process Engineer | Diagramas de plantas autorizadas | Sólo diagramas | No aprueba PFMEA |

Planes, ítems, versiones e historial se autorizan mediante su documento de origen. Parámetros mediante el producto. Los borradores se separan por usuario, planta, tipo e ID de documento.

Plantas, departamentos, categorías y unidades requieren Administrator para modificaciones. Véase contracts/endpoint-inventory.md para el inventario generado.

RLS añade aislamiento de filas; los permisos de operación se aplican en el servidor. La cuenta de aplicación debe ser NOSUPERUSER, NOBYPASSRLS y no ser propietaria de tablas. El usuario final no recibe credenciales SQL: el servidor establece el contexto después de validar sesión y planta.
