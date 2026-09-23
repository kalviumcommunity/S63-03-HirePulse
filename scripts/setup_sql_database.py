"""Initialize the local PostgreSQL assignment database and apply its SQL layer."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "database" / "postgres_data"
LOG_FILE = ROOT / "database" / "postgres.log"
DATABASE_NAME = "hirepulse_sql"
DATABASE_USER = "hirepulse"
PORT = "55432"


def executable(name: str) -> str:
    candidates = [shutil.which(name)]
    for version in ("18", "17", "16", "15"):
        candidates.append(f"C:/Program Files/PostgreSQL/{version}/bin/{name}.exe")
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise FileNotFoundError(f"PostgreSQL executable not found: {name}")


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def database_exists(psql: str) -> bool:
    result = subprocess.run(
        [psql, "-h", "localhost", "-p", PORT, "-U", DATABASE_USER, "-d", "postgres", "-Atc", "SELECT 1 FROM pg_database WHERE datname='hirepulse_sql';"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "1"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="Reinitialize the local cluster and database")
    args = parser.parse_args()

    initdb = executable("initdb")
    pg_ctl = executable("pg_ctl")
    createdb = executable("createdb")
    psql = executable("psql")

    if args.reset and DATA_DIR.exists():
        raise RuntimeError("Refusing to delete the database cluster automatically; remove database/postgres_data manually first.")

    if not (DATA_DIR / "PG_VERSION").exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        run([initdb, "-D", str(DATA_DIR), "-U", DATABASE_USER, "-A", "trust", "--no-locale"])

    status = subprocess.run([pg_ctl, "-D", str(DATA_DIR), "status"], capture_output=True, text=True)
    if status.returncode != 0:
        run([pg_ctl, "-D", str(DATA_DIR), "-o", f"-p {PORT}", "-l", str(LOG_FILE), "start"])

    if not database_exists(psql):
        run([createdb, "-h", "localhost", "-p", PORT, "-U", DATABASE_USER, DATABASE_NAME])

    for sql_file in (
        ROOT / "database" / "schema.sql",
        ROOT / "database" / "views" / "vw_active_customers.sql",
        ROOT / "database" / "views" / "vw_revenue_by_region.sql",
        ROOT / "database" / "aggregations" / "agg_daily_metrics.sql",
    ):
        run([psql, "-h", "localhost", "-p", PORT, "-U", DATABASE_USER, "-d", DATABASE_NAME, "-v", "ON_ERROR_STOP=1", "-f", str(sql_file)])

    print(f"Database ready: postgresql+psycopg2://{DATABASE_USER}@localhost:{PORT}/{DATABASE_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())