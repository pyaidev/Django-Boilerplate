#!/bin/sh
set -eu
umask 077
mkdir -p backups
backup_tmp="$(mktemp "backups/postgres-$(date -u +%Y%m%dT%H%M%SZ).partial.XXXXXX")"
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' > "$backup_tmp"
mv "$backup_tmp" "$backup_tmp.dump"
printf 'Backup saved: %s\n' "$backup_tmp.dump"
