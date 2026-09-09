# Backup and recovery

Run `make backup` to create a private PostgreSQL custom-format dump in backups/.
The directory is ignored by Git and excluded from Docker images. Copy backups to a
separate encrypted storage location and set a retention policy.

Validate a backup with pg_restore --list. Regularly test restoration into a **new empty
database**, never the live database:

```sh
docker compose exec db sh -c 'createdb -U "$POSTGRES_USER" restore_check'
docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d restore_check --no-owner --exit-on-error' < backups/your-backup.dump
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d restore_check -c "SELECT count(*) FROM django_migrations;"'
```

Choose a new database name if restore_check already exists. A restore test must also check
representative application records and permissions. The commands above do not replace
the live database. Remove the temporary restore database only after validating its name.

Back up media_data separately if using local media, or enable versioning/backup on the S3
bucket. Database dumps do not contain media objects, Grafana state or Redis queues.
Dashboard definitions already live in Git. Back up Grafana's named volume if UI-managed
users/settings matter. Preserve .env/secrets in your secret manager, not in this repository.

The legacy postgres_data directory remains on disk and is not mounted by Compose.
Untracking it preserves local files but does not remove old Git history.
