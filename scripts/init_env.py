"""Generate local Docker credentials without overwriting an existing .env."""

import os
import secrets
from pathlib import Path

root = Path(__file__).resolve().parent.parent
target = root / ".env"
template = (root / ".env-example").read_text()
for placeholder, size in (
    ("CHANGE_ME_SECRET_KEY", 64),
    ("CHANGE_ME_POSTGRES_PASSWORD", 32),
    ("CHANGE_ME_GRAFANA_PASSWORD", 32),
):
    template = template.replace(placeholder, secrets.token_urlsafe(size))
try:
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    print(".env already exists; preserved.")
else:
    with os.fdopen(descriptor, "w") as stream:
        stream.write(template)
    print("Created .env with random local credentials (permissions 0600).")
