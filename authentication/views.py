from rest_framework import generics, status, permissions
from .serializers import (
    RegisterSerializer,
    SetNewPasswordSerializer,
    logoutSerializer,
    EmailVerificationSerializer,
    LoginSerializer,
    ChangPasswordSerializer,
    RequestRestPasswordSerializer,
    RequestVerifyEmailSerializer,
)
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import TokenError, RefreshToken
from django.contrib.auth import get_user_model
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import views
import jwt
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str
from django.utils.http import urlsafe_base64_decode
from .emails import verify_email_task, reset_password_email_task

User = get_user_model()
SITE_URL = settings.SITE_URL
SECRET_KEY = settings.SECRET_KEY


class RegisterView(generics.GenericAPIView):
    """
    Register a new user with email and password
    Permissions: AllowAny
    """

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user = request.data
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Send verification email
        verify_email_task.delay(serializer.data["email"])
        return Response(
            {
                "success": True,
                "message": "User created successfully and sent verification url",
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmail(views.APIView):
    serializer_class = EmailVerificationSerializer
    permission_classes = [permissions.AllowAny]

    token_param_config = openapi.Parameter(
        "token",
        in_=openapi.IN_QUERY,
        description="Description",
        type=openapi.TYPE_STRING,
    )

    @swagger_auto_schema(manual_parameters=[token_param_config])
    def get(self, request):
        token = request.GET.get("token")
        valid = False
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=payload["user_id"])
            if not user.email_verified:
                user.email_verified = True
                user.save()
            valid = True
        except:
            valid = False

        return render(request, "auth/complete_active_email.html", {"valid": valid})


class LoginAPIView(generics.GenericAPIView):
    """
    Login user with email and password
    Permissions: AllowAny
    """

    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutAPIView(generics.GenericAPIView):
    """
    Logout user
    Permissions: IsAuthenticated
    """

    serializer_class = logoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            token = RefreshToken(request.data.get("refresh"))
            token.blacklist()

        except TokenError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class RequestPasswordReset(generics.GenericAPIView):
    """
    Request password reset
    Permissions: IsAuthenticated
    """

    serializer_class = RequestRestPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.data.get("email")

        if User.objects.filter(email=email).exists():
            # Send reset password email
            reset_password_email_task.delay(email)
            return Response(
                {"success": "We have sent you a link to reset your password"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Email does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ChangPasswordAPIView(generics.GenericAPIView):
    """
    Change password by providing old password and new password
    Permissions: IsAuthenticated
    """

    serializer_class = ChangPasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.data.get("new_password"))
        user.save()
        return Response(
            {"success": True, "message": "Password change success"},
            status=status.HTTP_200_OK,
        )
