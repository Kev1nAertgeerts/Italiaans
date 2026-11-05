# italiaans

Django 6.1 web application (Python 3.12) with PostgreSQL, Gunicorn, WhiteNoise and a shared Traefik v3 reverse proxy.

- `PROJECT_NAME` (Django package): `italiaans`
- `DEPLOYMENT_NAME` (Docker/Traefik/host paths): `italiaans`

## Layout

```text
.
├── django/
│   ├── manage.py
│   ├── contexts_processors.py
│   ├── italiaans/          # project package (settings, urls, wsgi)
│   ├── apps/               # core, accounts
│   ├── static/  media/  templates/
├── Dockerfile  docker-compose.yml  entrypoint.sh  wait_for_db.py  gunicorn.conf.py
├── requirements.txt  .env.example
```

Apps use import-safe dotted paths (`apps.core`, `apps.accounts`). `accounts` provides a custom `User` model (`phone`, `email`) and a login page at `/accounts/login/`. Health check: `/health/`.

## Local development (no Docker, Gunicorn or Traefik)

```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env      # Windows: copy .env.example .env
# edit .env: set SECRET_KEY (optional while DEBUG=True)

cd django
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open <http://127.0.0.1:8000/> or <http://localhost:8000/>.

With `POSTGRES_HOST` empty and `DEBUG=True`, SQLite (`db.sqlite3` in the project root) is used. To use PostgreSQL locally, set `POSTGRES_HOST=localhost` plus the other `POSTGRES_*` values.

Run tests: `cd django && python manage.py test`.

## Production (Hetzner, Docker Compose, shared Traefik)

Prerequisites on the host:

1. The external Docker network `traefik-public` exists and the shared Traefik v3 is running (entrypoint `websecure`, cert resolver `letsencrypt`, file middleware `secure-headers`). Do not create these networks from this project.
2. The shared PostgreSQL server is reachable and the database/user exist.
3. The media directory exists: `sudo mkdir -p /mnt/HC_Volume_105814616/italiaans/media`.
4. The production env file exists and is protected:

```bash
sudo mkdir -p /etc/italiaans
sudo cp .env.example /etc/italiaans/.env
sudo nano /etc/italiaans/.env       # DEBUG=False, SECRET_KEY, POSTGRES_*, POSTGRES_HOST=postgres-shared, passwords
sudo chown root:root /etc/italiaans/.env
sudo chmod 600 /etc/italiaans/.env
```

The env file is injected with `env_file` and is never copied into the image.

Deploy:

```bash
docker compose --env-file /etc/italiaans/.env config   # validate
docker compose --env-file /etc/italiaans/.env up -d --build
```

`--env-file` is needed because Compose interpolation (`DOMAIN`, `HETZNER_VOLUME_PATH`, `POSTGRES_DOCKER_NETWORK`) is separate from the service `env_file`.

Updating: `git pull && docker compose --env-file /etc/italiaans/.env up -d --build`.

On start the container waits for PostgreSQL, runs migrations and `collectstatic`, creates the superuser from `DJANGO_SUPERUSER_*` if missing, and starts Gunicorn on internal port 8000.

### PostgreSQL network

`web` is attached only to `traefik-public`. If the shared PostgreSQL is reachable only through the Docker network named by `POSTGRES_DOCKER_NETWORK`, uncomment `- database` under `web.networks` in `docker-compose.yml`.

### Useful commands

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```
