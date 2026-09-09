# Django Docker Boilerplate

Django 5.2 LTS / Python 3.13 starter with PostgreSQL, Redis, session authentication,
OpenAPI 3, Celery, Grafana and Prometheus. Dependencies are pinned in `uv.lock`
and exported with hashes for Docker builds.

## Start with Docker

Requirements: Docker with Compose v2, and Python 3 to generate local credentials.

```sh
make up
docker compose exec app python manage.py createsuperuser
```

`make up` generates a private `.env` if missing, builds the app, applies migrations
in a separate one-shot service, and waits for healthy services. Existing `.env`
files are preserved. The default configuration is for localhost over HTTP.

| Service | Address |
| --- | --- |
| Django admin | http://localhost:8001/admin/ |
| Swagger / OpenAPI 3 | http://localhost:8001/swagger/ |
| ReDoc | http://localhost:8001/redoc/ |
| API schema | http://localhost:8001/api/schema/ |
| Liveness / readiness | http://localhost:8001/health/live/ and /health/ready/ |
| Grafana | http://localhost:3000/ |
| Prometheus | http://localhost:9090/ |

Grafana's username is `admin`. Its randomly generated password is
`GRAFANA_ADMIN_PASSWORD` in your local `.env`. The **Boilerplate → Django / API Overview**
dashboard and Prometheus datasource are provisioned automatically.

Only localhost ports are published. PostgreSQL, Redis and the dedicated metrics port
are accessible inside the Compose network. Existing `postgres_data/` files are not
used or modified: Docker uses a fresh named volume.

## Included components

- Custom User from the first migration; register/login/logout/me and password reset.
- Session authentication with CSRF protection, including anonymous login/register requests.
- Private Notes CRUD: ownership filtering, bounded pagination, search and filters.
- Redis-backed atomic rate limits, plus django-axes protection for repeated login failures.
- django-simple-history for Note changes, visible in the admin.
- WhiteNoise static serving with compressed, hashed assets generated during image build.
- Optional private S3 media storage through django-storages/boto3.
- Celery worker and database-backed Celery Beat scheduler.
- Request IDs and JSON logs, optional Sentry integration, dependency health endpoints.
- Prometheus metrics across all Gunicorn workers, provisioned Grafana dashboard and alert rules.
- pytest, Redis concurrency tests, Ruff, pre-commit, CI and dependency update configuration.

## Layout

```text
apps/
  accounts/             User model, auth endpoints, reset email task
  common/               BaseModel, health endpoints, maintenance tasks
  notes/                Example business app: model, serializers, views, history
core/
  settings/             base, development, production, test, build
  celery.py             Celery application
  checks.py             Environment checks
  throttling.py         Shared atomic request limits
  middleware.py         Request IDs and request logging
  schema.py             OpenAPI routes
tests/                  Auth, permissions, rate limits, health, production checks
monitoring/
  prometheus/           Scrape configuration and alert rules
  grafana/              Provisioned datasource and dashboard
scripts/                Local environment setup and database backup
docs/                   API usage, production, monitoring and recovery
```

Keep each business domain in its own `apps/<domain>/`. Add `services.py` for multi-step
business operations when needed. This starter's simple CRUD does not require a
repository layer or separate microservices.

## Authentication and API

See [API guide](docs/api.md) for CSRF/session examples and the rate-limit table.
Swagger is public in local development and restricted to staff in production.

All endpoints are under `/api/v1/`. Failed API requests use:

```json
{"error":{"code":"throttled","message":"Request was throttled.","details":{},"request_id":"..."}}
```

## Tests and development

Full integration tests in Docker, with real PostgreSQL and Redis:

```sh
docker compose --profile test run --build --rm test
```

Fast local checks (requires Python 3.13 and uv):

```sh
uv sync --frozen
make lint check test
uv run pre-commit install
```

Local unit tests use isolated SQLite and memory cache. The real Redis test is skipped
unless `TEST_REDIS_URL` is supplied; Docker and CI enable it. Do not point test URLs
at a production database. Django creates a separate test database.

Change dependencies in `pyproject.toml`, then run `make lock`. Commit `uv.lock` and
both exported requirements files together. Production images exclude development packages.

## Operations

```sh
docker compose logs --tail=100 -f app worker
docker compose exec app python manage.py check
docker compose exec app celery -A core inspect ping
make backup
make down
```

`make down` preserves named volumes. Do not add `-v` unless you intend to delete
the database, media, Redis state and monitoring data.

- [Production deployment](docs/production.md)
- [Monitoring and rate limits](docs/monitoring.md)
- [Backup and recovery](docs/backup.md)

This repository previously tracked PostgreSQL binary files. They were removed from
the Git index and ignored while preserving the local directory. Existing Git history
still contains them; inspect that history separately before publishing the repository.

