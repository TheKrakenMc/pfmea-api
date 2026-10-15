# Migración y reversión controladas

Esta entrega no ejecutó migraciones contra la base existente del usuario ni publicó servicios. El ensayo local usa datos sintéticos. La ejecución en otro entorno requiere destino y acceso explícitos, como establece el plan aprobado.

## Preparación

1. Identificar versión de PostgreSQL, esquema pfmea, historial de migraciones y cuenta de ejecución. Separar la cuenta DBA que migra de la cuenta de aplicación que atiende solicitudes.
2. Reservar la ventana de mantenimiento y detener escrituras. Guardar código y configuración de ambas versiones para una reversión compatible.
3. Configurar una variable de conexión de respaldo autorizada. scripts/database_backup.py no lee .env ni imprime credenciales. Requiere pg_dump/pg_restore compatibles con el servidor.
4. Crear respaldo en una carpeta privada:

    python -m scripts.database_backup backup --connection-env BACKUP_DATABASE_URL --archive ruta/previo.dump

5. Crear una base de restauración vacía y descartable; nunca usar el origen como destino. El script rechaza un destino donde ya exista el esquema pfmea:

    python -m scripts.database_backup restore --connection-env RESTORE_TEST_DATABASE_URL --archive ruta/previo.dump

El manifiesto guarda SHA-256 y conteos de todas las tablas. Restaurar verifica ambos. Completar además el smoke test de documentos, usuarios y relaciones sobre la copia. Mantener el respaldo protegido; en Windows aplicar las ACL privadas del entorno.

## Ensayo y aplicación

Sobre la copia restaurada, configurar DATABASE_URL con una cuenta de migración y ejecutar python run_migrations.py. El runner usa un bloqueo asesor PostgreSQL, comprueba checksums y confirma cada SQL junto con su registro de historial.

Historial heredado: si existen registros sin checksum, el runner se detiene. Revisar manualmente los archivos frente a la evidencia de despliegue; sólo entonces se permite python run_migrations.py --adopt-legacy-checksums. Esa adopción establece una línea base; no demuestra retrospectivamente que se aplicó el mismo SQL en el pasado.

Migraciones nuevas V4_030–V4_037:

- Sesiones, asignaciones de plantas, tokens consumidos y control de versiones.
- Vínculos y datos operativos de controles; coincidencias ambiguas se conservan y señalan.
- RLS de plantas, proyectos y relaciones; revisión histórica preservada.
- Orden estable de pasos, intentos de recuperación y revisión de procedencias.
- Integridad de productos versionados.

No se recalculan ni reabren automáticamente los documentos aprobados. Los registros afectados se marcan para revisión. Las sesiones anteriores dejan de ser aceptadas: los tokens deben pertenecer a una sesión persistida nueva.

Antes de habilitar el nuevo login, revisar administradores heredados creados con credenciales compartidas. Reemplazar sus contraseñas con python -m scripts.provision_admin --reset-existing, que solicita el nuevo secreto sin imprimirlo, revoca sesiones y exige cambio al ingresar. No basta con eliminar la contraseña del código: los hashes de cuentas existentes se conservan hasta ejecutar ese paso en la ventana autorizada. No se modificaron contraseñas reales durante esta auditoría.

Tras el ensayo, ejecutar pruebas de permisos, concurrencia, aprobaciones, exportación y recuperación de borradores. Revisar registros ambiguos de control_plan_items con needs_review. Sólo después aplicar en la ventana acordada, configurar la cuenta runtime restringida y validar readiness.

## Cuenta de ejecución

La cuenta runtime necesita uso del esquema y secuencias y permisos de aplicación sobre tablas, pero debe ser NOSUPERUSER, NOBYPASSRLS y no ser su propietaria. No usar la cuenta DBA como DATABASE_URL de la aplicación. La API valida sesión/planta y establece el contexto de autorización mediante parámetros SQL; el navegador no establece ese contexto.

## Reversión

Si la validación falla, detener escrituras. Restaurar el respaldo verificado en un destino vacío, comprobar conteos y relaciones y volver a desplegar conjuntamente las versiones compatibles de API e interfaz. No ejecutar un down que borre evidencias o revisiones nuevas. Si se permitieron escrituras después de migrar, reconciliarlas antes de restaurar para no perderlas.

## Evidencia disponible y límites

PGlite comprobó migraciones aditivas, preservación de documentos sintéticos, restauración y RLS de un rol restringido. scripts/verify_postgres.py y CI preparan la prueba de bloqueo con dos conexiones PostgreSQL nativas; no se afirma que esa ejecución nativa haya pasado mientras no exista su resultado. Tampoco se afirma haber respaldado o restaurado datos reales del usuario.
