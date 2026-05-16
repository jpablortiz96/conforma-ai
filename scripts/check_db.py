"""Check the Conforma-AI database schema after migrations."""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings

EXPECTED_TABLES = {"audits", "ai_systems", "agent_runs", "artifacts", "gaps"}


def main() -> int:
    """Inspect the configured database and print a schema summary."""

    settings = get_settings()
    engine = create_engine(settings.database_url)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    missing = sorted(EXPECTED_TABLES - tables)
    extra = sorted(tables - EXPECTED_TABLES)

    print(f"database_url={settings.database_url}")
    print(f"tables={sorted(tables)}")
    if missing:
        print(f"missing={missing}")
    if extra:
        print(f"extra={extra}")

    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
