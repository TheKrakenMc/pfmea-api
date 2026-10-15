"""Explicit backup/restore tool. Never reads .env; never prints connection credentials."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlsplit, parse_qs, unquote
import psycopg2
from psycopg2 import sql


def connection(name):
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"Required connection environment variable: {name}")
    return value.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )


def client_environment(url):
    parts = urlsplit(url)
    environment = os.environ.copy()
    environment.update(
        PGHOST=parts.hostname or "",
        PGPORT=str(parts.port or 5432),
        PGUSER=unquote(parts.username or ""),
        PGPASSWORD=unquote(parts.password or ""),
        PGDATABASE=unquote(parts.path.lstrip("/")),
    )
    for key, value in parse_qs(parts.query).items():
        if key == "sslmode":
            environment["PGSSLMODE"] = value[0]
    return environment


def counts(url):
    with psycopg2.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname='pfmea' ORDER BY tablename"
            )
            tables = [row[0] for row in cur.fetchall()]
            result = {}
            for table in tables:
                cur.execute(
                    sql.SQL("SELECT count(*) FROM {}.{}").format(
                        sql.Identifier("pfmea"), sql.Identifier(table)
                    )
                )
                result[table] = cur.fetchone()[0]
            return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["backup", "restore"])
    parser.add_argument("--connection-env", required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    url = connection(args.connection_env)
    archive = args.archive.resolve()
    manifest = archive.with_suffix(archive.suffix + ".manifest.json")
    if args.action == "backup":
        if archive.exists() or manifest.exists():
            raise RuntimeError("Refusing to overwrite an existing backup")
        executable = shutil.which("pg_dump")
        if not executable:
            raise RuntimeError("pg_dump is required")
        before = counts(url)
        archive.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                executable,
                "--format=custom",
                "--no-owner",
                "--no-acl",
                "--file",
                str(archive),
            ],
            env=client_environment(url),
            check=True,
            capture_output=True,
        )
        after = counts(url)
        if before != after:
            raise RuntimeError(
                "Source counts changed; repeat backup in the maintenance window"
            )
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        manifest.write_text(
            json.dumps({"sha256": digest, "counts": before}, indent=2), encoding="utf-8"
        )
        os.chmod(archive, 0o600)
        os.chmod(manifest, 0o600)
        print("Backup and checksum manifest created")
    else:
        recorded = json.loads(manifest.read_text(encoding="utf-8"))
        if hashlib.sha256(archive.read_bytes()).hexdigest() != recorded["sha256"]:
            raise RuntimeError("Backup checksum mismatch")
        with psycopg2.connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname='pfmea')"
                )
                if cur.fetchone()[0]:
                    raise RuntimeError(
                        "Restore requires a disposable empty target without pfmea schema"
                    )
        executable = shutil.which("pg_restore")
        if not executable:
            raise RuntimeError("pg_restore is required")
        subprocess.run(
            [
                executable,
                "--exit-on-error",
                "--no-owner",
                "--no-acl",
                "--dbname",
                client_environment(url)["PGDATABASE"],
                str(archive),
            ],
            env=client_environment(url),
            check=True,
            capture_output=True,
        )
        if counts(url) != recorded["counts"]:
            raise RuntimeError("Restored table counts do not match backup manifest")
        print("Restore verified: checksum and table counts match")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        raise SystemExit(str(error)) from None
    except Exception as error:
        raise SystemExit(
            f"Backup/restore failed ({type(error).__name__}); inspect the operation securely"
        ) from None
