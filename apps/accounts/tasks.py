from celery import shared_task
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import send_mail
from django.template.loader import render_to_string


@shared_task(autoretry_for=(OSError,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def send_password_reset(email):
    # Queued for both known and unknown addresses to keep the HTTP response uniform.
    form = PasswordResetForm({"email": email})
    if not form.is_valid():
        return
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.encoding import force_bytes
    from django.utils.http import urlsafe_base64_encode

    for user in form.get_users(email):
        context = {
            "base_url": settings.PUBLIC_BASE_URL,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": default_token_generator.make_token(user),
        }
        send_mail(
            "Reset your password",
            render_to_string("registration/password_reset_email.txt", context),
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
