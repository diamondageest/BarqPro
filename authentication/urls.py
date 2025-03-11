from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path("signup/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginAPIView.as_view(), name="login"),
    path("logout/", views.LogoutAPIView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "password/change/", views.ChangPasswordAPIView.as_view(), name="change_password"
    ),
    # Reset Password
    path(
        "password/request-reset/",
        views.RequestPasswordReset.as_view(),
        name="request_reset_password",
    ),
    # Verify Email
    path("email/verify/", views.VerifyEmail.as_view(), name="email_verify"),
]
