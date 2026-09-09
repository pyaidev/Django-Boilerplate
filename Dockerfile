FROM python:3.13-slim-bookworm AS dependencies
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements/base.txt requirements/base.txt
RUN pip install --no-cache-dir --require-hashes -r requirements/base.txt

FROM python:3.13-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH"
WORKDIR /app
COPY --from=dependencies /opt/venv /opt/venv
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app
COPY --chown=app:app . .
RUN mkdir -p /app/static /app/media && chown -R app:app /app/static /app/media
USER app
RUN DJANGO_SETTINGS_MODULE=core.settings.build python manage.py collectstatic --noinput
EXPOSE 8000 9000
ENTRYPOINT ["sh", "/app/entrypoint.sh"]
CMD ["gunicorn", "--config", "gunicorn.conf.py", "core.wsgi:application"]

FROM runtime AS test
USER root
COPY requirements/dev.txt requirements/dev.txt
RUN pip install --no-cache-dir --require-hashes -r requirements/dev.txt
USER app
ENV DJANGO_SETTINGS_MODULE=core.settings.test
CMD ["pytest", "-q", "-p", "no:cacheprovider"]
