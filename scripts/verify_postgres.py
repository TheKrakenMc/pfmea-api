"""Run only against a fresh disposable database explicitly supplied for integration."""

import os
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import psycopg2

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("PFMEA_TEST_DATABASE_URL")
if not URL:
    raise RuntimeError(
        "PFMEA_TEST_DATABASE_URL must name a fresh disposable PostgreSQL database; no .env fallback"
    )


def runtime_connection():
    conn = psycopg2.connect(URL)
    with conn.cursor() as cur:
        cur.execute(
            "SET search_path=pfmea,public; SET ROLE pfmea_runtime; SELECT set_config('app.current_user_id','1',false),set_config('app.current_plant_id','1',false),set_config('app.is_admin','false',false)"
        )
    conn.commit()
    return conn


def main():
    conn = psycopg2.connect(URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname='pfmea')"
            )
            if cur.fetchone()[0]:
                raise RuntimeError(
                    "Refusing a database that already contains the pfmea schema"
                )
            cur.execute("CREATE SCHEMA pfmea;SET search_path=pfmea,public")
            cur.execute((ROOT / "tests/fixtures/current_schema.sql").read_text())
            cur.execute((ROOT / "tests/fixtures/security_seed.sql").read_text())
            cur.execute(
                "DROP TABLE auth_sessions;DROP TABLE user_plants;DROP TABLE used_verification_tokens"
            )
            for table in ["pfmea_headers", "flowcharts", "control_plans", "products"]:
                cur.execute(
                    f"ALTER TABLE {table} DROP COLUMN lock_version,DROP COLUMN needs_review"
                )
            cur.execute(
                "ALTER TABLE pfmea_worksheet_rows DROP COLUMN validated_by,DROP COLUMN validated_at; ALTER TABLE user_otps DROP COLUMN attempts"
            )
            for column in [
                "pfmea_worksheet_row_id",
                "source_row_id",
                "needs_review",
                "characteristic",
                "classification",
                "specification",
                "unit_id",
                "measurement_method",
                "sample_size",
                "sample_frequency",
                "responsible_person_id",
                "reaction_plan",
                "is_active",
                "source_reviewed",
                "source_review_reason",
            ]:
                cur.execute(f"ALTER TABLE control_plan_items DROP COLUMN {column}")
        conn.commit()
        for migration in sorted((ROOT / "migrations").glob("V4_03[0-7]_*.sql")):
            with conn.cursor() as cur:
                cur.execute(migration.read_text())
            conn.commit()
        with conn.cursor() as cur:
            cur.execute(
                "CREATE ROLE pfmea_runtime NOSUPERUSER NOBYPASSRLS;GRANT USAGE ON SCHEMA pfmea TO pfmea_runtime;GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA pfmea TO pfmea_runtime;GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA pfmea TO pfmea_runtime"
            )
        conn.commit()
        first = runtime_connection()
        second = runtime_connection()
        try:
            with first.cursor() as cur:
                cur.execute("SELECT id FROM pfmea_headers ORDER BY id")
                assert cur.fetchall() == [(1,)]
                cur.execute("SELECT id FROM control_plan_items ORDER BY id")
                assert cur.fetchall() == [(1,)]
                cur.execute("SELECT set_config('app.current_plant_id','2',false)")
                cur.execute("SELECT count(*) FROM pfmea_headers")
                assert cur.fetchone()[0] == 0
                cur.execute("SELECT set_config('app.current_plant_id','1',false)")
                cur.execute(
                    "SELECT lock_version FROM pfmea_headers WHERE id=1 FOR UPDATE"
                )
                assert cur.fetchone()[0] == 1

            def stale_editor():
                with second.cursor() as cur:
                    cur.execute("SET LOCAL lock_timeout='5s'")
                    cur.execute(
                        "SELECT lock_version FROM pfmea_headers WHERE id=1 FOR UPDATE"
                    )
                    version = cur.fetchone()[0]
                    if version != 1:
                        second.rollback()
                        return "conflict"
                    raise AssertionError(
                        "Concurrent editor unexpectedly retained obsolete revision"
                    )

            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(stale_editor)
                time.sleep(0.2)
                assert not future.done()
                with first.cursor() as cur:
                    cur.execute(
                        "UPDATE pfmea_headers SET lock_version=lock_version+1 WHERE id=1"
                    )
                first.commit()
                assert future.result(timeout=6) == "conflict"
            print(
                "Native PostgreSQL: migrations, restricted-role RLS and concurrent editors passed"
            )
        finally:
            first.close()
            second.close()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
