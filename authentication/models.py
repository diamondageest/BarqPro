from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.db import models
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.services.utils import check_subscription_status



class User(AbstractUser):
    username = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("username"),
    )
    email = models.EmailField(
        _("Email Address"),
        unique=True,
        db_index=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    # verify user email status
    email_verified = models.BooleanField(default=False)

    # verify profile completed status
    profile_completed = models.BooleanField(default=False, db_index=True)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []


    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ("-date_joined",)
        indexes = [
            models.Index(fields=["id", "username"]),
        ]

    @property
    def current_subscription(self):
        """
        Return the current subscription of the user.
        None if the user has no subscription.
        """
        from accounts.serializers import PaymentSerializer, FreeTierSerializer

        # Check if the user has an active subscription or free tier
        subscription_status = check_subscription_status(self)

        if subscription_status["free_tier_active"]:
            return FreeTierSerializer(
                {
                    "expiration_date": subscription_status["free_days_ago"].isoformat(),
                }
            ).data
        elif subscription_status["last_payment_active"]:
            first_payment = subscription_status["last_payment"]
            return PaymentSerializer(first_payment).data
        elif last_payment := self.subscriptions.last():
            return PaymentSerializer(last_payment).data

        return None

    def __str__(self):
        return self.email

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}
