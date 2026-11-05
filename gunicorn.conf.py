import multiprocessing
import os
from pathlib import Path

# Run from the directory containing manage.py and the project package.
chdir = str(Path(__file__).resolve().parent / "django")

bind = "0.0.0.0:8000"
workers = int(os.environ.get("WEB_CONCURRENCY", min(multiprocessing.cpu_count() * 2 + 1, 9)))
timeout = 60
graceful_timeout = 30
keepalive = 5
accesslog = "-"
errorlog = "-"
forwarded_allow_ips = "*"  # Only reachable through the shared Traefik proxy.
