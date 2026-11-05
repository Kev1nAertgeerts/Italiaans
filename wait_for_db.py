"""Block until PostgreSQL accepts connections (not just until the container is up)."""

import os
import sys
import time

import psycopg2

host = os.environ.get("POSTGRES_HOST", "").strip()
if not host:
    print("POSTGRES_HOST not set; skipping database wait.")
    sys.exit(0)

timeout = int(os.environ.get("DB_WAIT_TIMEOUT", "60"))
deadline = time.monotonic() + timeout

while True:
    try:
        connection = psycopg2.connect(
            dbname=os.environ.get("POSTGRES_DB", ""),
            user=os.environ.get("POSTGRES_USER", ""),
            password=os.environ.get("POSTGRES_PASSWORD", ""),
            host=host,
            port=os.environ.get("POSTGRES_PORT", "5432"),
            connect_timeout=3,
        )
        connection.close()
        print("PostgreSQL is accepting connections.")
        break
    except psycopg2.OperationalError as exc:
        if time.monotonic() >= deadline:
            print(f"PostgreSQL not available after {timeout}s: {exc}", file=sys.stderr)
            sys.exit(1)
        print("Waiting for PostgreSQL...")
        time.sleep(2)
