from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.urls import reverse
from django.utils.encoding import smart_bytes
from celery import shared_task
from django.core.mail import send_mail

User = get_user_model()

# Constants
SITE_URL = settings.SITE_URL
SECRET_KEY = settings.SECRET_KEY
EMAIL_FROM = settings.EMAIL_FROM


def send_email_task(data):
    try:
        send_mail(
            subject=data["email_subject"],
            message=data["email_body"],
            from_email=EMAIL_FROM,
            recipient_list=[data["to_email"]],
            fail_silently=False,
        )
        return "Email sent successfully"
    except Exception as e:
        # Handle exceptions
        print(f"Failed to send email =>> Error: {str(e)}")


@shared_task(name="verify_email_task")
def verify_email_task(user_email):
    try:
        user = User.objects.get(email=user_email)
        token = RefreshToken.for_user(user).access_token
        user_name = user.email.split("@")[0]
        verify_url = SITE_URL + "/api/auth/email/verify/?token=" + str(token)

        email_body = (
            "Hello "
            + str(user_name)
            + "\n Use the URL below to verify your email \n"
            + str(verify_url)
            + "\n The URL will be expired in 15 minutes"
            + "\n\n  If you didn't request this, please ignore this email."
            + "\n Best regards, FatooraPro Team"
        )
        data = {
            "email_body": email_body,
            "to_email": user.email,
            "email_subject": "Verify your email",
        }
        send_email_task(data)
    except Exception as e:
        # Handle exceptions
        print(f"Failed to send email =>> Error: {str(e)}")


@shared_task(name="reset_password_email_task")
def reset_password_email_task(user_email):
    try:
        user = User.objects.get(email=user_email)
        uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
        token = PasswordResetTokenGenerator().make_token(user)
        user_name = user.email.split("@")[0]
        relativeLink = reverse(
            "rest_password", kwargs={"uidb64": uidb64, "token": token}
        )

        URL = SITE_URL + relativeLink

        email_body = (
            "Hello "
            + str(user_name)
            + "\n Use URL below to reset your password  \n"
            + str(URL)
            + "\n The URL will be expired in 15 minutes"
            + "\n\n  If you didn't request this, please ignore this email."
            + "\n Best regards, FatooraPro Team"
        )
        data = {
            "email_body": email_body,
            "to_email": user.email,
            "email_subject": "Reset your password",
        }
        send_email_task(data)
    except Exception as e:
        # Handle exceptions
        print(f"Failed to send email =>> Error: {str(e)}")
