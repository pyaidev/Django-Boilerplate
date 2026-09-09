import logging

from celery import shared_task
from django.core.management import call_command


@shared_task
def healthcheck():
    logging.getLogger(__name__).info("Celery healthcheck completed")
    return "ok"


@shared_task
def clear_expired_sessions():
    call_command("clearsessions")
