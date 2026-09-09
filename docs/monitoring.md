# Monitoring

Prometheus scrapes app:9000 every 15 seconds. Gunicorn's master exposes a separate HTTP
metrics server, and each worker writes counters/histograms to a per-master temporary
directory. The multiprocess collector aggregates every worker. A fresh directory is
created on restart, preventing stale process data; counters reset across app restarts.

Port 9000 is not published on the host and /metrics is absent from the public Django URL
configuration. Grafana and Prometheus bind only to localhost. Protect access through
an authenticated gateway if you later expose them.

The provisioned **Django / API Overview** dashboard includes availability, request rate,
status codes, p95 latency, server errors, 429 responses, database queries and cache gets.
Generate a few API requests and allow two scrape intervals for rate panels to populate.

Prometheus rules:
- DjangoDown: scrape failure for one minute.
- DjangoHighErrorRate: server errors exceed 5% for five minutes.
- DjangoRateLimitSpike: more than one 429 response/second for five minutes.

Rules appear in Prometheus → Alerts. Notification delivery is not configured; connect
an Alertmanager/receiver when you choose a destination. Application readiness covers
PostgreSQL, cache and rate-limit Redis; scrape availability alone is not full dependency
readiness. Container health status is available with docker compose ps.

Validation:
```sh
docker compose exec prometheus promtool check config /etc/prometheus/prometheus.yml
docker compose exec prometheus promtool check rules /etc/prometheus/alerts.yml
docker compose exec app celery -A core inspect ping
```

Dashboards and datasource definitions are versioned under monitoring/grafana.
Edit those files to make lasting changes. Prometheus retains at most 15 days / 2 GB;
rebuild the monitoring images after changing their configuration.
Grafana and Prometheus state live in named volumes.
