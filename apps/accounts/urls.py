from django.urls import path

from . import views

app_name = "accounts"
urlpatterns = [
    path("csrf/", views.CSRFView.as_view(), name="csrf"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("me/", views.MeView.as_view(), name="me"),
    path("password-reset/", views.PasswordResetView.as_view(), name="password-reset"),
    path(
        "password-reset/confirm/", views.PasswordResetConfirmAPIView.as_view(), name="password-reset-confirm"
    ),
]
