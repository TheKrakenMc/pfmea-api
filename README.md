# PFMEA API

API FastAPI + SQLAlchemy + PostgreSQL para productos, diagramas de proceso, PFMEA y planes de control. La interfaz está en el repositorio hermano pfmea-ui.

## Funcionamiento

El usuario inicia sesión con contraseña. Cada solicitud valida la sesión persistida, el rol, la planta autorizada y la relación con el proyecto. Los documentos se guardan con una revisión esperada; una copia obsoleta recibe 409. Los cambios y la auditoría se confirman juntos. Los aprobados son inmutables y sus snapshots se conservan al reabrir.

Python es la referencia provisional de AP. Alto riesgo significa AP H o severidad ≥ 9 por decisión del proyecto. El cierre requiere evidencia, responsable, fecha, reevaluación y validación de Owner. No se declara certificación ni conformidad normativa automática.

## Desarrollo

Crear un entorno virtual e instalar requirements-lock.txt para reproducir el entorno auditado. Copiar .env.example y configurar una base de desarrollo propia. Antes de iniciar una base existente, seguir docs/migration-runbook.md sobre respaldo y ensayo.

    python -m pip install -r requirements-lock.txt
    python run_migrations.py
    python -m scripts.provision_admin
    python -m uvicorn app.main:app --reload

El aprovisionamiento pregunta la contraseña sin imprimirla. El arranque de la API no migra ni crea administradores. No hay ruta pública de migración ni OTP de login. La verificación de correo y recuperación de contraseña se mantienen separadas.

Health: /api/v1/health. Readiness: /api/v1/readiness; devuelve 503 si la base, esquema o cuenta de ejecución requerida no están disponibles.

## Calidad y contratos

    python -m ruff check app scripts tests
    python -m pytest -q
    python -m compileall -q app scripts
    python -m scripts.export_contracts

CI incluye integración PostgreSQL nativa en una base efímera. Véase docs/local-verification.md para las diferencias entre SQLite, PGlite y PostgreSQL nativo, y para la auditoría visual sintética.

- docs/permission-matrix.md: permisos y plantas.
- docs/contracts/endpoint-inventory.md: inventario generado por endpoint.
- docs/contracts/openapi.json: contrato API generado.
- docs/migration-runbook.md: mantenimiento, respaldo y reversión.
- docs/traceability-review.md: trazabilidad y límites normativos.
- docs/baseline y docs/legacy-source: fuentes históricas conservadas fuera del runtime.
