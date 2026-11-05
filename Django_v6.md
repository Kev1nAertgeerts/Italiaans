# [AGENTS.md](http://AGENTS.md)

## Project Identity — EDIT ONLY HERE FOR A NEW PROJECT

Set these two values before running the agent. These are **agent template inputs**, not automatically exported shell environment variables:

```env
PROJECT_NAME=italiaans
DEPLOYMENT_NAME=italiaans
```

- `PROJECT_NAME`: valid Python package identifier for the Django project (e.g. `italiaans`).
- `DEPLOYMENT_NAME`: lowercase deployment identifier for Traefik routers/services, host paths, database name, and Compose project name (e.g. `italiaans`); use only safe letters, digits, underscores or hyphens, starting with a letter.
- These two lines are the **single source of truth** for project identity. All later occurrences of `${PROJECT_NAME}` and `${DEPLOYMENT_NAME}` in this document refer to these values; do not ask the user to replace names elsewhere.
- The agent MUST resolve these values when generating files, including `.env.example`, Docker Compose labels, README commands, and host directory paths. A Markdown file does not itself interpolate variables.
- The agent MUST generate concrete usable values where shell/Compose interpolation is not supported (especially Traefik label keys). Keep Docker service `web` and the external `traefik-public` network unchanged.
- Domain-specific settings such as `DOMAIN` and `LETSENCRYPT_EMAIL` remain independent configuration values; never assume every deployment has the same domain.

---

## Project Overview

This is a Django web application.

The agent should:

- create and maintain a Django project
- use Docker and Docker Compose
- use Traefik as reverse proxy
- automatically configure HTTPS using Let's Encrypt
- prepare the project for production deployment
- keep the project structure clean and minimal

---

## Tech Stack

- Python 3.12
- Django latest stable
- PostgreSQL
- Gunicorn
- WhiteNoise
- Shared Traefik v3 reverse proxy
- Docker Compose

---

## Configurable Project Name

The Django project name must be configurable.
PROJECT_NAME refers ONLY to the Django Python package/project directory.
It must not automatically rename Docker services, volumes, or Traefik routers.

Use the two values in **Project Identity** at the top of this document. Do not define or edit them again here.

The agent must:

- never hardcode the Django project name
- use PROJECT_NAME consistently everywhere
- use PROJECT_NAME in imports, paths, Gunicorn, settings, and startup scripts

Example:

```bash
django-admin startproject ${PROJECT_NAME} .
```

Gunicorn example:

```bash
gunicorn ${PROJECT_NAME}.wsgi:application
```

---



## Initial Setup Tasks

When initializing the project, the agent should:

1. Create Django project using configurable project name
2. Create `requirements.txt`
3. Create `.gitignore`
4. Create `.env.example`
5. Create Docker setup
6. Configure Gunicorn
7. Configure WhiteNoise
8. Configure Docker labels for shared Traefik integration
9. Configure static files
10. Configure production settings
11. Create README.md with setup instructions

---



## Required Files

The agent must create:

- requirements.txt
- .gitignore
- .dockerignore
- docker-compose.yml
- Dockerfile
- .env.example
- gunicorn.conf.py
- README.md

---



## Required Startup Files

The agent must create:

- entrypoint.sh

The startup flow must wait until PostgreSQL accepts connections, not only until the container starts.

The agent must create:

- wait_for_db.py

---



## Django Standards

- Use environment variables for secrets
- DEBUG must come from environment variables
- ALLOWED_HOSTS must come from environment variables
- Use PostgreSQL in production
- Separate settings if needed
- Use pathlib for paths
- Configure WhiteNoise middleware
- Configure STATIC_ROOT
- Run collectstatic during deployment
- Never commit `.env` files

Required Django security settings:

- SECURE_SSL_REDIRECT
- SESSION_COOKIE_SECURE
- CSRF_COOKIE_SECURE
- SECURE_HSTS_SECONDS
- SECURE_HSTS_INCLUDE_SUBDOMAINS
- SECURE_HSTS_PRELOAD

settings.py MUST include:

```python
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Brussels"
USE_I18N = True
USE_TZ = True
```

---



## Development Media URLs

During development, Django must serve media files using:

```python
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```



## Required Django Applications

The agent must ALWAYS create the following Django applications during initialization:

- core
- accounts

Applications must be created inside:

```text
django/apps/
```

Required structure:
django/
├── apps/
│   ├── core/
│   │   ├── **init**.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── tests.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── migrations/
│   │
│   └── accounts/
│       ├── **init**.py
│       ├── admin.py
│       ├── apps.py
│       ├── models.py
│       ├── tests.py
│       ├── views.py
│       ├── urls.py
│       ├── migrations/

---



## Mandatory Centralized Django Templates — Strict Rule

All Django HTML templates MUST be stored exclusively inside `django/templates/`.

- NEVER create a `templates/` directory inside any Django application, including `django/apps/core/`, `django/apps/accounts/`, or any future app.
- Organize app-specific templates in central namespaced subdirectories, such as `django/templates/core/home.html` and `django/templates/accounts/login.html`.
- Shared templates such as `base.html` belong directly in `django/templates/` or suitable subdirectories beneath it.
- In `${PROJECT_NAME}/settings.py`, configure `TEMPLATES` with `"DIRS": [BASE_DIR / "templates"]` and `"APP_DIRS": False`.
- Render templates with their namespaced paths, such as `render(request, "accounts/login.html")`.
- When updating an existing project, move all app-level templates into the central directory, preserve namespaces, update references as necessary, and delete empty app-level template directories. Never overwrite files or discard templates during migration.
- Before completion, verify that no `django/apps/**/templates/` directory exists, run `python manage.py check`, and test that the required pages render successfully.
- This rule is mandatory for all existing and future apps and supersedes any conflicting template-location instructions.

---



## Required Accounts Login Page

The agent MUST create a working Django login page for the `accounts` app, including a function-based view, URL route, and HTML template. Keep all other requirements unchanged.

Required template path: `django/templates/accounts/login.html`. Use the namespaced template path `accounts/login.html` and ensure `APP_DIRS=False` in Django `TEMPLATES`.

Create the following function in `django/apps/accounts/views.py` (or equivalent function-based implementation with the same behavior):

```python
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    error = None
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get("next") or request.GET.get("next")
            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect("home")
        error = "Invalid username or password."

    return render(request, "accounts/login.html", {
        "error": error,
        "next": request.POST.get("next") or request.GET.get("next", ""),
    })
```

- The generated `core` app MUST provide a URL named `home`, or adapt the post-login redirect to an existing, valid named URL. Never leave a broken redirect.
- Create `django/apps/accounts/urls.py` with:

```python
from django.urls import path
from .views import login_view

urlpatterns = [
    path("login/", login_view, name="login"),
]
```

- Keep the root URL include `path("accounts/", include("apps.accounts.urls"))`, resulting in `/accounts/login/`.
- In `${PROJECT_NAME}/settings.py`, add:

```python
LOGIN_URL = "/accounts/login/"
```

- Generate a usable `accounts/login.html` with a `<form method="post">`, `{% csrf_token %}`, `username` and `password` fields, a submit button, an error message when authentication fails, and a hidden `next` input when provided. Do not hardcode credentials or disable CSRF protection.
- Ensure Django sessions, authentication and messages middleware/apps remain enabled.
- Test that GET `/accounts/login/` renders, invalid credentials do not authenticate, valid credentials log the user in, and `@login_required` redirects to `LOGIN_URL`.

---



## Required Custom User Model (accounts)

The agent MUST create a custom Django user model **before the first migration** in `django/apps/accounts/models.py`. The model MUST inherit from `django.contrib.auth.models.AbstractUser` and define both `phone` and `email` fields:

```python
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.username
```

Requirements:

- Set `AUTH_USER_MODEL = "accounts.User"` in the generated Django settings **before** running `makemigrations` or `migrate`. The Django app label is `accounts` even though its import path is `apps.accounts`.
- Generate and apply the initial `accounts` migration for the custom user model. Never switch from Django's default user model after initial migrations have been applied.
- For all user relationships use `settings.AUTH_USER_MODEL` (or `get_user_model()` where appropriate), not direct imports of `django.contrib.auth.models.User`.
- Register the custom model in `django/apps/accounts/admin.py` using Django's `UserAdmin`, so the custom fields can be managed in the admin interface. Include `phone` and `email` in the appropriate fieldsets and add forms.
- Preserve Django's default username-based authentication unless a later requirement explicitly changes it. `phone` is optional, and `email` uses Django's email field validation.
- Ensure the custom model works with superuser creation, including the environment-driven startup command.

---



## Force Import-Safe App Naming

Installed apps MUST use full dotted Python paths:

```python
INSTALLED_APPS = [
    ...
    "apps.core",
    "apps.accounts",
]
```

The agent must NEVER use:

- "core"
- "accounts"

because all apps are located inside:

```text
django/apps/
```

### Required AppConfig names

Every generated application inside `django/apps/<appname>/` MUST set its
`AppConfig.name` to the fully qualified Python import path `apps.<appname>`.
This applies to `core`, `accounts`, and every subsequently created app.

For example, `django/apps/core/apps.py` MUST contain:

```python
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
```

And `django/apps/accounts/apps.py` MUST use `name = "apps.accounts"`.
Never leave the default `name = "core"` or `name = "accounts"` generated by
`startapp`. The agent MUST verify and correct `apps.py` after creating each app.

---



## Python Package Requirements

The following file is REQUIRED:

```text
django/apps/__init__.py
```

This file must exist to ensure Python package discovery works correctly.

---



## Required Python Packages

The generated requirements.txt MUST include:

```text
Django
gunicorn
whitenoise
psycopg2-binary
Pillow
python-dotenv
```

---



## Django Folder Structure

The agent must place all Django-related code inside a dedicated `django/` directory.

Required structure:

```text
project-root/
├── django/
│   ├── manage.py
│   ├── contexts_processors.py
│   ├── PROJECT_NAME/
│   ├── apps/
│   ├── static/
│   ├── media/
│   └── templates/
```

Requirements:

- `manage.py` must live inside `django/`
- `contexts_processors.py` must live directly inside `django/` (keep this exact filename)
- the Django project package (`PROJECT_NAME`) must live inside `django/`
- all Django applications must live inside `django/apps/`
- shared templates must live inside `django/templates/`
- shared static files must live inside `django/static/`
- uploaded media files must live inside `django/media/`

### Required custom template context processor

The agent MUST create `django/contexts_processors.py` and register its callable in the Django `TEMPLATES` setting in `${PROJECT_NAME}/settings.py`. Use this exact filename and import path; do not silently rename it to `context_processors.py`.

Minimum generated file:

```python
# django/contexts_processors.py

def global_context(request):
    """Add shared template context values here."""
    return {}
```

In `${PROJECT_NAME}/settings.py`, retain Django's existing standard context processors and append the custom processor to the `context_processors` list under `TEMPLATES[0]["OPTIONS"]`:

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": False,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "contexts_processors.global_context",
            ],
        },
    },
]
```

- The callable must accept `request` and return a dictionary, even if initially empty.
- Ensure `django/` is on the Python import path in both local development and Docker, as already required elsewhere in this document.
- Validate the configuration with `python manage.py check` and a template render that uses the registered context processor.
- Preserve every other V3 requirement, including external Docker networks, the custom accounts user model, and production environment file handling.

The agent must correctly configure:

```python
BASE_DIR = Path(__file__).resolve().parent.parent.parent
```

The Docker container working directory should be:

```dockerfile
WORKDIR /app
```

Gunicorn must use:

```bash
gunicorn ${PROJECT_NAME}.wsgi:application
```

with:

```bash
cd /app/django
```

or equivalent configuration.

The Python path must correctly resolve imports from:

```text
django/apps/
```

The agent should automatically create apps using:

```bash
python manage.py startapp app_name django/apps/app_name
```

Installed apps should use:

```python
apps.core
apps.accounts
```

or equivalent import-safe structure.

```

```

---



## Docker Standards

All services should use restart policies unless-stopped.

The project must integrate with an existing shared Traefik reverse proxy.

The Django project must NOT create its own Traefik container.

The web service must connect to the external Docker network:

```yaml
networks:
  - traefik-public
```

Use multi-service docker compose:

Services:

- web

The web container should:

- run Django through Gunicorn
- expose port 8000 internally
- not expose Django directly to the internet

Expose Django only internally.
The Django project must not expose ports 80 or 443 directly.

Public HTTP/HTTPS traffic must be routed through the shared Traefik reverse proxy.

---



## Shared Docker Network — Mandatory Compose Layout

The generated `docker-compose.yml` MUST use the following network configuration. The `web` service MUST list **only** `traefik-public` under its `networks` key; do not add `internal` or `database` to that service by default.

```yaml
services:
  web:
    networks:
      - traefik-public

networks:
  traefik-public:
    external: true
  database:
    external: true
    name: ${POSTGRES_DOCKER_NETWORK:-postgres}
```

The final `networks:` mapping is a **top-level** Compose key, not a child of `services:`. Keep the `database` network definition for shared PostgreSQL infrastructure, but do not attach `web` to it unless the deployment explicitly requires that connection; if PostgreSQL is reachable only through that Docker network, add `database` to `web.networks` as a documented exception. Never create these external networks automatically, and never generate an `internal` network by default.

The agent MUST ensure the `traefik-public` network already exists on the host and MUST validate the resulting configuration using `docker compose config` before deployment.

---


## Shared Traefik Integration Requirements

The generated Docker Compose MUST use the exact network name:

```text
traefik-public
```

The agent must NEVER generate alternative network names such as:

- web
- proxy
- public
- nginx
- traefik

The web container MUST connect using:

```yaml
networks:
  - traefik-public
```

Do not add an `internal` network. Attach `database` only when required for PostgreSQL connectivity, as described in **Shared Docker Network — Mandatory Compose Layout**.

The Traefik Docker label MUST use (agent substitutes `${DEPLOYMENT_NAME}` in the label key when generating Compose):

```yaml
- traefik.docker.network=traefik-public
- traefik.http.routers.${DEPLOYMENT_NAME}.middlewares=secure-headers@file
```

The generated `docker-compose.yml` MUST define these top-level networks:

```yaml
networks:
  traefik-public:
    external: true
  database:
    external: true
    name: ${POSTGRES_DOCKER_NETWORK:-postgres}
```

Requirements:

NEVER generate additional Host() rules
NEVER add www redirects or aliases automatically
NEVER use:
||
&&
multiple Host() expressions
HostRegexp
www.${DOMAIN}
The router rule must contain ONLY a single Host() matcher
The generated label must remain simple and deterministic

Invalid examples:

Host(`${DOMAIN}`) || Host(`www.${DOMAIN}`)
HostRegexp(...)
Host(`${DOMAIN}`, `www.${DOMAIN}`)

Only this is allowed:

Host(`${DOMAIN}`)

and must NOT redefine the network name using:

```yaml
name:
```

The following is an **agent template**, not a literal final Compose file: substitute `${DEPLOYMENT_NAME}` in every Traefik label key before writing it. Compose variable interpolation does not apply to arbitrary YAML keys.

```yaml
labels:
  - traefik.enable=true

  - traefik.docker.network=traefik-public

  - traefik.http.routers.${DEPLOYMENT_NAME}.rule=Host(`${DOMAIN}`)
  - traefik.http.routers.${DEPLOYMENT_NAME}.entrypoints=websecure

  - traefik.http.routers.${DEPLOYMENT_NAME}.tls=true
  - traefik.http.routers.${DEPLOYMENT_NAME}.tls.certresolver=letsencrypt
  - traefik.http.routers.${DEPLOYMENT_NAME}.middlewares=secure-headers@file

  - traefik.http.services.${DEPLOYMENT_NAME}.loadbalancer.server.port=8000
```

The Django container must NOT expose ports 80 or 443.

Only the shared Traefik container should expose public HTTP/HTTPS ports.

The project must use the external Docker network:

```yaml
networks:
  traefik-public:
    external: true
```

Django must correctly trust reverse proxy SSL headers using:

```python
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
```

---



## Port Exposure Rules

The generated docker-compose.yml must NEVER expose:

```yaml
ports:
  - "80:80"
  - "443:443"
```

The Django web container must only expose port 8000 internally.

Only the shared Traefik reverse proxy may expose public HTTP/HTTPS ports.

---



## Docker API Compatibility

The host Docker Engine may use a modern Docker API version (currently 1.54).

Traefik must be compatible with the installed Docker Engine API version.

Requirements:

- use Traefik v3 latest stable
- never force old Docker API versions
- never use legacy Docker client settings
- use the Docker socket:
unix:///var/run/docker.sock
- ensure Traefik correctly negotiates the Docker API version automatically
- if necessary, explicitly set:
DOCKER_API_VERSION=1.54

The generated configuration must be compatible with:

- Docker Engine 29+
- Docker API 1.54+

---



## Gunicorn Requirements

- Use Gunicorn as the Django application server
- Bind internally on port 8000
- Run behind Traefik
- Use production-safe defaults
- Use multiple workers based on CPU count

---



## WhiteNoise Requirements

- Use WhiteNoise for static file serving
- Configure compressed manifest storage
- Run `collectstatic` during deployment
- Keep static configuration production-ready
- Configure STATIC_URL and STATIC_ROOT
- Configure MEDIA_URL and MEDIA_ROOT

settings.py MUST include:

```python
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

---



## Environment Variables

Expected variables (template notation below is for the **agent**; generate resolved literal values in `.env.example`, since `python-dotenv` and Docker Compose have different expansion behavior). `DOMAIN` may be customized independently of the project names. `ALLOWED_HOSTS` must use the final domain and local hostnames. Never write real passwords into `.env.example`:

```env
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=${DOMAIN},127.0.0.1,localhost,django.127.0.0.1,django.localhost

POSTGRES_DB=${DEPLOYMENT_NAME}
POSTGRES_USER=kevin
POSTGRES_PASSWORD=
POSTGRES_HOST=postgres-shared
POSTGRES_PORT=5432
POSTGRES_DOCKER_NETWORK=shared_internal

HETZNER_VOLUME_ROOT=/mnt/HC_Volume_105814616
HETZNER_VOLUME_PATH=/mnt/HC_Volume_105814616/${DEPLOYMENT_NAME}/media
PROJECT_NAME=${PROJECT_NAME}
DEPLOYMENT_NAME=${DEPLOYMENT_NAME}

DOMAIN=${DEPLOYMENT_NAME}.kevin-aertgeerts.be
LETSENCRYPT_EMAIL=admin@example.com
```

---



### Hetzner volume configuration

The generated `.env.example` MUST contain both:

```env
HETZNER_VOLUME_ROOT=/mnt/HC_Volume_105814616
HETZNER_VOLUME_PATH=/mnt/HC_Volume_105814616/${DEPLOYMENT_NAME}/media
```

The agent MUST substitute `${DEPLOYMENT_NAME}` with the value from **Project Identity** when writing a ready-to-use `.env.example` and absolute host media path. Never leave `<projectname>` in generated output. The volume must persist on the Hetzner host. In `docker-compose.yml`, reference `${HETZNER_VOLUME_PATH}` as a bind mount to `/app/django/media`.

`PROJECT_NAME` is only the Django Python package name; deployment infrastructure is named using `DEPLOYMENT_NAME`.

---

### Production environment file outside Docker

For production on Hetzner, the real `.env` MUST live on the HOST at:

```text
/etc/${DEPLOYMENT_NAME}/.env
```

The generated `docker-compose.yml` MUST load it in the web service with the **resolved absolute path** (shown here as an agent template):

```yaml
services:
  web:
    env_file:
      - /etc/${DEPLOYMENT_NAME}/.env
```

The agent must substitute the deployment name in the generated Compose file so the `env_file` path is concrete and usable.

The agent MUST:

- Never COPY, ADD, or bind-mount the production `.env` into the Docker image or container.
- Exclude `.env` and `.env.*` (except `.env.example`) from Git and the Docker build context.
- Document creating `/etc/${DEPLOYMENT_NAME}/` on the Hetzner host and protecting the file with restrictive permissions (for example `chmod 600` and appropriate ownership).
- Use `env_file` to inject the environment variables into the container process; understand that the values remain visible to processes with sufficient access, even though the file is not inside the container.
- Resolve the deployment name in the generated README commands and Compose `env_file` path. Compose interpolation variables such as `DOMAIN` and `HETZNER_VOLUME_PATH` must come from the host environment or from `docker compose --env-file /etc/RESOLVED_DEPLOYMENT_NAME/.env ...`; service-level `env_file` alone does NOT supply Compose interpolation.
- Document production commands such as `docker compose --env-file /etc/${DEPLOYMENT_NAME}/.env up -d --build`, or an equivalent command with `DEPLOYMENT_NAME` set on the host.
- Keep local non-Docker development working with a local `.env` loaded by `python-dotenv`; the external `/etc/` file is required only for production Docker deployment.
- Never commit actual passwords, keys, or other production secrets into `.env.example`.

---

## Environment Loading

The project must automatically load environment variables from a `.env` file during local development.

The agent should use:

- python-dotenv
or
- django-environ

If using python-dotenv, settings.py must include:

```python
from dotenv import load_dotenv
load_dotenv()
```

---



## Django Superuser

The project should support automatic superuser creation through environment variables.

Expected variables (template notation below is for the **agent**; generate resolved literal values in `.env.example`, since `python-dotenv` and Docker Compose have different expansion behavior). `DOMAIN` may be customized independently of the project names. `ALLOWED_HOSTS` must use the final domain and local hostnames. Never write real passwords into `.env.example`:

```env
DJANGO_SUPERUSER_USERNAME=kevin
DJANGO_SUPERUSER_EMAIL=kevin.aertgeerts1994@gmail.com
DJANGO_SUPERUSER_PASSWORD=change-me
```

The startup process may automatically create the superuser if it does not exist.

---



### Development

```bash
docker compose up --build
```



### Migrations

```bash
docker compose exec web python manage.py migrate
```



### Create superuser

```bash
docker compose exec web python manage.py createsuperuser
```

---



## Container Startup Flow

The web container should:

1. wait for PostgreSQL to become available
2. run database migrations
3. run collectstatic
4. start Gunicorn
5. expose Django internally on port 8000

The agent may create a custom Django management command:
createsuperuser_if_not_exists

Example startup sequence:

```bash
python manage.py migrate && \
python manage.py collectstatic --noinput && \
python manage.py createsuperuser_if_not_exists && \
gunicorn ${PROJECT_NAME}.wsgi:application
```

---



## Deployment Expectations

The deployment should:

- automatically collect static files
- serve static files through WhiteNoise
- run Django through Gunicorn behind Traefik
- automatically provision HTTPS certificates
- redirect HTTP to HTTPS
- support Docker Compose deployment
- work on Ubuntu VPS providers
- include container healthchecks

Production defaults:

- DEBUG=False
- secure cookies enabled
- CSRF protection enabled
- HSTS enabled
- secrets from environment variables only
- PostgreSQL used in production

---



## Deployment Workflow

The project must support simple Git-based deployments.

Typical deployment flow:

```bash
git pull
docker compose up -d --build
```

Requirements:

- If PostgreSQL is externally managed, persistence is handled by the external PostgreSQL infrastructure.
- Let's Encrypt certificates must persist
- rebuilding the web container must not destroy database data
- migrations should run automatically
- static files should rebuild automatically

---



## Persistent Storage

Docker volumes must persist:

- uploaded media files

Example:

```yaml
services:
  web:
    volumes:
      - ${HETZNER_VOLUME_PATH}:/app/django/media
```

---



## External Shared Services

The project may connect to externally managed services such as:

- shared PostgreSQL
- shared Redis
- shared Traefik

The agent must support Docker external networks for shared infrastructure services.

---



## Python Path Requirements

The Docker container must ensure the following path is available:

```bash
/app/django
```

The generated project must use relative paths whenever possible.

No source code may assume it is running inside `/app`.

Only Docker configuration may reference `/app`.

The container should configure:

```dockerfile
ENV PYTHONPATH=/app/django
```

or equivalent configuration.

This is required so imports like:

```python
apps.core
apps.accounts
```

## work correctly everywhere.



## Root URL Configuration

The root urls.py must include:

```python
path("", include("apps.core.urls")),
path("accounts/", include("apps.accounts.urls")),
```

---



## Shared PostgreSQL Requirements

The project must support using a shared external PostgreSQL server.

The generated docker-compose.yml must NOT automatically create a PostgreSQL container.

Database connections must come entirely from environment variables:

```env
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=
POSTGRES_PORT=
```

Example:

```env
POSTGRES_HOST=postgres-shared
POSTGRES_PORT=5432
```

The startup process must still wait until PostgreSQL accepts connections.

---



## Local Development Support

The generated project MUST support both local development and production deployment without requiring manual code changes.

---



### Local Development Mode

The project must be runnable directly from the Django development server without Docker, Gunicorn, or Traefik.

Example:

```bash
cd django
python manage.py migrate
python manage.py runserver
```

Requirements:

- The Django development server must work using `python manage.py runserver`.
- Docker must NOT be required for local development.
- Traefik must NOT be required for local development.
- Gunicorn must NOT be required for local development.
- The project must be accessible at:
  - [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
  - [http://localhost:8000/](http://localhost:8000/)

---



### Production Mode

The existing production deployment must remain unchanged.

Production must continue using:

- Docker Compose
- Gunicorn
- Shared Traefik reverse proxy
- HTTPS with Let's Encrypt
- WhiteNoise
- PostgreSQL

The production startup flow should remain:

1. Wait for PostgreSQL
2. Run migrations
3. Run collectstatic
4. Optionally create the superuser
5. Start Gunicorn

---



### Environment-Based Configuration

The generated project MUST automatically configure itself based on the value of `DEBUG`.

When:

```env
DEBUG=True
```

the project should:

- allow HTTP
- disable SSL redirects
- disable secure cookies
- disable HSTS
- support Django's development server

When:

```env
DEBUG=False
```

the project should:

- enable SSL redirects
- enable secure cookies
- enable CSRF secure cookies
- enable HSTS
- trust the reverse proxy using:

```python
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
```

---



### Database Configuration

The project must obtain all database settings from environment variables.

Example for local development:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Example for production:

```env
POSTGRES_HOST=postgres-shared
POSTGRES_PORT=5432
```

The project must never hardcode database hosts.

---



### Docker Independence

The Django source code must never depend on Docker or Traefik.

Traefik configuration must exist only inside Docker Compose labels.

The Django application must run identically whether started with:

```bash
python manage.py runserver
```

or

```bash
gunicorn ${PROJECT_NAME}.wsgi:application
```

The only differences between development and production should come from environment variables.

---



### README Requirements

The generated README.md must document both startup methods.

---



#### Local Development

```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt

cd django

python manage.py migrate
python manage.py runserver
```

---



#### Production

```bash
docker compose --env-file /etc/${DEPLOYMENT_NAME}/.env up -d --build
```

The agent must render `${DEPLOYMENT_NAME}` to the configured concrete name in the generated README command. The production host must have the external environment file before deployment.

The agent must always generate projects that support both workflows without requiring modifications after project creation.

---



### Local Development Requirements

The generated project must include everything required for local development.

The agent should generate:

- `.env.example` suitable for local development.
- A `.venv`-friendly project layout.
- A `requirements.txt` that supports both local development and production.
- A README describing local setup.
- No Docker dependency for normal Django development.

---



## Success Criteria

Every generated project MUST work immediately in both modes.

Local Development:

```bash
python manage.py migrate
python manage.py runserver
```

Production:

```bash
docker compose up -d --build
```

No code changes should ever be required when switching between these two modes.

Only environment variables should differ.

---



## Healthchecks

All containers should include healthchecks where appropriate.

Examples:

- web container health endpoint

```python
path("health/", health_check_view)
```

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
  interval: 30s
  timeout: 10s
  retries: 5
```

---

