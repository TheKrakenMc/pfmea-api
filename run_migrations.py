"""Explicit, serialized, checksummed SQL migrations. Never run from API lifespan."""
import argparse
import hashlib
import os
import re
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

LOCK_KEY = 734992601

def transaction_sql(source):
    # Existing files wrap their SQL in transaction statements. The runner owns the transaction.
    return re.sub(r"(?im)^\s*(BEGIN|COMMIT|ROLLBACK)\s*;\s*$", "", source)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adopt-legacy-checksums",action="store_true",help="Record baseline checksums only after manual verification of legacy migrations")
    args=parser.parse_args()
    load_dotenv()
    url = os.environ.get("DATABASE_URL", "").strip().strip('"').strip("'")
    if not url:
        raise RuntimeError("DATABASE_URL is required")
    url = url.replace("postgresql+psycopg2://", "postgresql://").replace("postgresql+asyncpg://", "postgresql://")
    root = Path(__file__).resolve().parent
    conn = psycopg2.connect(url)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_lock(%s)", (LOCK_KEY,))
            cur.execute("CREATE SCHEMA IF NOT EXISTS pfmea")
            cur.execute("SET search_path TO pfmea, public")
            cur.execute("SELECT to_regclass('pfmea.roles')")
            if cur.fetchone()[0] is None:
                sql = (root / "PFMEA_v2.sql").read_text(encoding="utf-8")
                cur.execute(transaction_sql(re.sub(r"\btimestampz\b", "timestamptz", sql, flags=re.I)))
            cur.execute("CREATE TABLE IF NOT EXISTS migration_history (id SERIAL PRIMARY KEY, migration_name VARCHAR(255) UNIQUE NOT NULL, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            cur.execute("ALTER TABLE migration_history ADD COLUMN IF NOT EXISTS checksum varchar(64)")
        conn.commit()
        for path in sorted((root / "migrations").glob("*.sql")):
            source = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(source.encode()).hexdigest()
            with conn.cursor() as cur:
                cur.execute("SELECT checksum FROM migration_history WHERE migration_name=%s", (path.name,))
                recorded = cur.fetchone()
                if recorded:
                    if recorded[0] and recorded[0] != checksum:
                        raise RuntimeError(f"Applied migration changed: {path.name}")
                    if recorded[0] is None:
                        if not args.adopt_legacy_checksums:
                            raise RuntimeError("Legacy migration checksum missing; review history before explicit baseline adoption")
                        cur.execute("UPDATE migration_history SET checksum=%s WHERE migration_name=%s", (checksum,path.name))
                else:
                    cur.execute(transaction_sql(source))
                    cur.execute("INSERT INTO migration_history(migration_name,checksum) VALUES (%s,%s)", (path.name,checksum))
            conn.commit()
            print(f"Verified migration: {path.name}")
    except RuntimeError:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise RuntimeError("Migration failed; transaction rolled back. Inspect database diagnostics securely.") from None
    finally:
        # Closing the connection releases the session advisory lock, including on failure.
        conn.close()

if __name__ == "__main__":
    main()
