# Production

The default Compose configuration runs locally over HTTP. For production, set in `.env`:

```dotenv
DJANGO_SETTINGS_MODULE=core.settings.production
DEBUG=0
ALLOWED_HOSTS=api.example.com,localhost,127.0.0.1
PUBLIC_BASE_URL=https://api.example.com
CSRF_TRUSTED_ORIGINS=https://api.example.com
TRUST_PROXY_HTTPS=1
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=1
DEFAULT_FROM_EMAIL=noreply@example.com
```

Set SMTP credentials and use a fresh random SECRET_KEY. Configure a TLS reverse proxy
in front of localhost:8001 that validates the Host, redirects HTTP to HTTPS, overwrites
X-Forwarded-Proto and X-Real-IP, limits request body size, and does not expose port 9000.
Set TRUSTED_PROXY_IPS to the exact direct peer address Django sees, not a broad subnet.
TRUST_PROXY_HTTPS must remain off unless the trusted proxy sanitizes the protocol header.

Production refuses a short key, wildcard hosts, SQLite, missing Redis or an HTTP public URL.
Secure session/CSRF cookies and HTTPS redirects are enabled. HSTS initially uses one hour;
increase after verifying TLS. Health endpoints are exempt from HTTPS redirects for
container probes and reveal only availability.

```sh
docker compose build app
docker compose run --rm app python manage.py check --deploy
docker compose up -d --wait
```

Run migrations once per release. The Compose migrate service completes before the app,
worker and beat start. Multiple hosts require release coordination; do not run concurrent
migration jobs. Run a single Beat scheduler. PostgreSQL version is pinned to major 16;
plan explicit upgrades with backups instead of switching to a different major's data files.

The initial HSTS profile intentionally leaves subdomain enforcement and preload off.
Deployment checks report security.W005/W021 for those choices. After verifying HTTPS on
all subdomains, you may enable SECURE_HSTS_INCLUDE_SUBDOMAINS=1 and, if you intend to join
the browser preload list, SECURE_HSTS_PRELOAD=1 with SECURE_HSTS_SECONDS=31536000.
The full HSTS profile is also covered by strict deployment checks in the test suite.

## Static and uploaded files

WhiteNoise serves static assets compressed and hashed from the image; collectstatic runs
during build using core.settings.build. This works with DEBUG=False without a separate
static server. Rebuild the image when assets change.

WhiteNoise does not serve user uploads. By default they use the media_data volume; configure
the reverse proxy or switch the default storage to S3:

```dotenv
USE_S3=1
AWS_STORAGE_BUCKET_NAME=your-private-bucket
AWS_S3_REGION_NAME=your-region
```

Prefer workload IAM credentials. AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY can be supplied
through your secret manager when needed. An S3-compatible service can use AWS_S3_ENDPOINT_URL.
Objects are private, use signed URLs, and do not overwrite existing filenames. Provision the
bucket and access policy separately; this project does not create cloud resources.
The Notes example has no upload endpoint.

## Errors, jobs and audit history

Set SENTRY_DSN to enable error reporting in production. Default PII collection is disabled
and tracing is off unless SENTRY_TRACES_SAMPLE_RATE is set. JSON request logs include
method, resolved route, status, duration and request ID rather than payloads/query strings.

Celery jobs use JSON, bounded execution times, and no persistent results by default.
Password reset emails are queued. Beat schedules are managed in admin → Periodic tasks;
an example maintenance task is apps.common.tasks.clear_expired_sessions.
The scheduler is installed without creating unsolicited recurring jobs.

Note history records creation, changes and deletion with the acting user. Bulk ORM updates
and raw SQL bypass model history; use the package's history-aware bulk helpers if needed.
User passwords are not stored in historical models.

## Existing databases

This starter introduces AUTH_USER_MODEL=accounts.User in the first migration. Compose
uses a new named volume and does not reuse the old postgres_data directory. If you need
an existing application's auth_user data, design and test a migration in a separate copy
before using this schema. Do not attach existing data to the new app without that migration.
