# Verificación local reproducible

Desde pfmea-api:

    python -m pip install -r requirements-lock.txt
    python -m ruff check app scripts tests
    python -m pytest -q
    python -m compileall -q app scripts
    python -m scripts.export_test_schema
    python -m scripts.export_contracts
    python -m pip_audit

Usar el Python del entorno virtual. Las pruebas API usan SQLite en memoria y notificaciones desactivadas. No migran DATABASE_URL.

Desde pfmea-ui, con ambos repositorios como hermanos:

    node scripts/verify-postgres.mjs

Ese ensayo usa PostgreSQL WASM (PGlite): prepara datos sintéticos anteriores a la actualización, respalda y restaura, aplica migraciones y prueba RLS con un rol restringido. El respaldo generado no representa datos del usuario.

El ensayo nativo scripts/verify_postgres.py sólo acepta PFMEA_TEST_DATABASE_URL explícita y rechaza bases que ya contengan el esquema pfmea. CI proporciona una base efímera y prueba dos conexiones concurrentes. Docker local no estuvo disponible: la ejecución nativa queda pendiente hasta obtener evidencia de CI o de un PostgreSQL local descartable.

Interfaz:

    npm ci
    npm run typecheck
    npm run lint
    npm run test -- --run
    npm run build
    npm audit

Para navegador, iniciar python -m scripts.audit_server desde pfmea-api. Publica sólo en 127.0.0.1:8014, con datos sintéticos en memoria. Configurar VITE_API_BASE_URL=http://localhost:8014/api/v1 e iniciar Vite en 127.0.0.1:5174. Ejecutar node scripts/audit-ui.mjs desde pfmea-ui. La cuenta sintética descrita en el script no existe en la base real.

Capturas y reportes: pfmea-ui/audit-artifacts/ui. No contienen datos reales.

Otros ensayos de navegador: node scripts/audit-flow.mjs (flujo integrado), node scripts/audit-edit.mjs (borradores/concurrencia/virtualización) y node scripts/audit-pdf.mjs (exportación). Se ejecutan desde pfmea-ui; audit-flow debe preceder a audit-pdf para crear el plan aprobado sintético. La cadena SQL completa se verifica con node scripts/verify-migration-chain.mjs.
