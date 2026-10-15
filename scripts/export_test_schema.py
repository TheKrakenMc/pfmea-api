"""Export ORM DDL for an isolated migration rehearsal; never connects to a database."""

from pathlib import Path
from sqlalchemy import create_mock_engine
from app.models import Base

statements = []
engine = create_mock_engine(
    "postgresql://",
    lambda statement, *a, **k: statements.append(
        str(statement.compile(dialect=engine.dialect)) + ";"
    ),
)
Base.metadata.create_all(engine)
target = Path(__file__).resolve().parents[1] / "tests/fixtures/current_schema.sql"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text("\n".join(statements), encoding="utf-8")
print("Exported isolated ORM schema")
