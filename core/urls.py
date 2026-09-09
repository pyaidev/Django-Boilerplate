from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import PasswordResetCompleteView
from django.urls import include, path

from apps.accounts.views import BrowserPasswordResetConfirmView
from apps.common.views import live, ready
from core.schema import swagger_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/live/", live, name="health-live"),
    path("health/ready/", ready, name="health-ready"),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.notes.urls")),
    path(
        "accounts/reset/<uidb64>/<token>/",
        BrowserPasswordResetConfirmView.as_view(),
        name="password-reset-browser",
    ),
    path("accounts/reset/done/", PasswordResetCompleteView.as_view(), name="password_reset_complete"),
    *swagger_urlpatterns,
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
