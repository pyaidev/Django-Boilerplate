from django.contrib.auth import login, logout
from django.contrib.auth.views import PasswordResetConfirmView
from django.middleware.csrf import get_token
from drf_spectacular.utils import extend_schema
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    CSRFSerializer,
    LoginSerializer,
    MessageSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .tasks import send_password_reset


class CSRFSessionAuthentication(SessionAuthentication):
    def authenticate(self, request):
        # DRF normally checks CSRF only after authentication. Login also needs it.
        self.enforce_csrf(request)
        return super().authenticate(request)


class PublicAuthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CSRFSessionAuthentication]


class CSRFView(PublicAuthView):
    @extend_schema(responses=CSRFSerializer)
    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class RegisterView(CreateAPIView):
    permission_classes = [AllowAny]
    authentication_classes = [CSRFSessionAuthentication]
    serializer_class = RegisterSerializer
    throttle_scope = "register"


class LoginView(PublicAuthView):
    throttle_scope = "login"

    @extend_schema(request=LoginSerializer, responses=UserSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request._request, user)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        logout(request._request)
        return Response(status=204)


class MeView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user


class PasswordResetView(PublicAuthView):
    throttle_scope = "password_reset"

    @extend_schema(request=PasswordResetSerializer, responses={202: MessageSerializer})
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        send_password_reset.delay(serializer.validated_data["email"])
        return Response({"detail": "If the account exists, a reset email will be sent."}, status=202)


class PasswordResetConfirmAPIView(PublicAuthView):
    throttle_scope = "password_reset_confirm"

    @extend_schema(request=PasswordResetConfirmSerializer, responses=MessageSerializer)
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Password updated. You can now log in."})


class BrowserPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "registration/password_reset_confirm.html"
    success_url = "/accounts/reset/done/"
