.PHONY: init up down logs test check lint lock migrations backup
init:
	python3 scripts/init_env.py
up: init
	docker compose up --build -d --wait
down:
	docker compose down
logs:
	docker compose logs --tail=100 -f app worker
test:
	uv run --frozen pytest
check:
	uv run --frozen python manage.py check --settings=core.settings.test
	uv run --frozen python manage.py makemigrations --check --dry-run --settings=core.settings.test
lint:
	uv run --frozen ruff check .
	uv run --frozen ruff format --check .
lock:
	uv lock
	uv export --frozen --no-dev --format requirements-txt --output-file requirements/base.txt --quiet
	uv export --frozen --format requirements-txt --output-file requirements/dev.txt --quiet
migrations:
	docker compose run --rm migrate
backup:
	sh scripts/backup.sh
