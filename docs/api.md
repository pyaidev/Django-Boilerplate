# API usage

This starter uses browser sessions. Cookie authentication requires CSRF protection.
Native/mobile token authentication can be added separately if the project needs it.

## Session flow

1. GET `/api/v1/auth/csrf/`, preserving the `csrftoken` cookie.
2. Read `csrfToken` from the response and send it as `X-CSRFToken` on unsafe requests.
3. POST `/api/v1/auth/register/` with username, email and password.
4. POST `/api/v1/auth/login/` with username and password.
5. Fetch CSRF again after login: Django rotates the CSRF secret.
6. Include the session cookie and CSRF header on writes.

For same-origin browser JavaScript:

```javascript
async function csrf() {
  const response = await fetch("/api/v1/auth/csrf/", {credentials: "same-origin"});
  return (await response.json()).csrfToken;
}
async function post(url, data) {
  return fetch(url, {
    method: "POST",
    credentials: "same-origin",
    headers: {"Content-Type": "application/json", "X-CSRFToken": await csrf()},
    body: JSON.stringify(data)
  });
}
await post("/api/v1/auth/login/", {username: "alice", password: "your-password"});
const response = await post("/api/v1/notes/", {title: "My note", body: "Private content"});
```

Separate browser origins need explicit CORS and CSRF trusted origins. Cookie policies
must also fit the deployment; the defaults assume same-site sessions.

## Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | /api/v1/auth/csrf/ | Obtain CSRF token |
| POST | /api/v1/auth/register/ | Create user; does not grant staff privileges |
| POST | /api/v1/auth/login/ | Start session |
| POST | /api/v1/auth/logout/ | End session |
| GET, PATCH | /api/v1/auth/me/ | Profile; only first/last name are editable |
| POST | /api/v1/auth/password-reset/ | Queue reset email; same response for unknown email |
| POST | /api/v1/auth/password-reset/confirm/ | Set password with uid, token, password |
| GET, POST | /api/v1/notes/ | List/create own notes |
| GET, PUT, PATCH, DELETE | /api/v1/notes/{id}/ | Read/change/delete own note |

Another user's note returns 404. Supplying an `owner` or staff flags cannot change ownership
or privileges. Filters: `?search=hello&is_archived=false&ordering=-created_at&limit=20&offset=0`.
The maximum page size is 100.

Reset emails link to a CSRF-protected HTML form. Tokens expire in one hour and stop
working after a password change. In local Docker, emails appear in worker logs;
configure SMTP before production. A Celery worker must be running.

## Rate limits

| Scope | Default | Environment variable |
| --- | --- | --- |
| Anonymous API | 60/minute per IP | RATE_ANON |
| Authenticated API | 600/minute per user | RATE_USER |
| Login | 5/minute per IP | RATE_LOGIN |
| Register | 5/hour per IP | RATE_REGISTER |
| Password reset request | 5/hour per IP | RATE_PASSWORD_RESET |
| Password reset confirm | 10/minute per IP | RATE_PASSWORD_RESET_CONFIRM |

Endpoint limits apply in addition to the general API limit. Counters are atomic Redis
operations shared across processes and instances using the same Redis URL. Each window
starts with the first request and expires without being extended by rejected attempts.
This is a fixed-window policy: traffic can burst around a window boundary.

A rejected request returns HTTP 429, `Retry-After` in seconds, and an error code.
Redis failure returns 503 instead of silently disabling protection. Development without
Redis uses process-local counters; production requires Redis.

By default only the direct peer IP is trusted. Configure `TRUSTED_PROXY_IPS` with exact
proxy peer addresses and make the proxy overwrite `X-Real-IP`. Arbitrary client
`X-Forwarded-For` and `X-Real-IP` headers cannot change the rate-limit identity.

Django-axes additionally locks a username/IP pair after five failed logins for 15 minutes,
including admin login. Reset a specific lock in the admin or with
`python manage.py axes_reset_ip_username <ip> <username>`.

API throttles are application controls. Apply connection/body-size limits at the reverse
proxy for traffic that never reaches a valid API view.
