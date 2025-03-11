from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid
from .services.utils import check_subscription_status
from .services.validators import NumericLengthValidator, VatValidator
from django.core.validators import MaxValueValidator
from .services.constants import PAYMENT_STATUS
from django.conf import settings

DAYS_BEFORE_RENEWAL = settings.DAYS_BEFORE_RENEWAL

User = get_user_model()


class Account(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="account", db_index=True
    )

    # organization Identification
    organization = models.CharField(
        max_length=255, null=True, help_text="Organization name in english"
    )
    register_number = models.CharField(max_length=255, null=True)
    tax_number = models.CharField(
        max_length=15,
        null=True,
        validators=[NumericLengthValidator(field_name="Tax Number", length=15)],
        db_index=True,
    )

    # Address information
    country = models.CharField(
        max_length=3, default="SA", null=True, help_text="Country code"
    )
    city = models.CharField(max_length=255, null=True, help_text="City name in english")
    street = models.CharField(
        max_length=255, null=True, help_text="Street name in english"
    )

    # additional info
    phone = models.CharField(max_length=30, null=True)
    taxable = models.BooleanField(default=True)
    vat = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=Decimal("15.0"),
        help_text="VAT percentage",
        validators=[VatValidator()],
    )
    # not required info
    logo = models.ImageField(upload_to="logos/", null=True, blank=True)

    def clean(self):
        # Check if the logo file size exceeds the maximum allowed size (in bytes)
        max_logo_size = 1024 * 1024  # 1 MB
        if self.logo and self.logo.size > max_logo_size:
            raise ValidationError("Logo size exceeds the maximum allowed size (1 MB).")

        super().clean()


    def save(self, *args, **kwargs):
        if self.taxable == False:
            self.vat = Decimal("0.0")
        else:
            self.vat = Decimal("15.0")

        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.user.email


class Package(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Price in SAR per month"
    )
    zatca_related = models.BooleanField(
        default=False,
        help_text="If true, the package will be related to ZATCA usage",
    )

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-created_at"]


class PaymentHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscriptions"
    )
    package = models.ForeignKey(
        Package, on_delete=models.SET_NULL, null=True, related_name="subscriptions"
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    duration = models.IntegerField(
        help_text="Duration in months",
        # validators=[MaxValueValidator(6, "Maximum duration is 6 months")],
    )

    status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS, default="pending", db_index=True
    )

    expiration_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    # persistent package info
    package_name = models.CharField(max_length=100, null=True, blank=True)
    package_description = models.TextField(null=True, blank=True)
    package_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    package_zatca_related = models.BooleanField(default=False)

    # payment info if available
    discount = models.IntegerField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    @property
    def is_expiry(self):
        if self.expiration_date is None:
            return None
        return self.expiration_date < timezone.now() and self.status == "completed"

    @property
    def can_subscribe(self):
        if self.expiration_date is None:
            return None

        # Calculate the date DAYS_BEFORE_RENEWAL days ago from the expiration date
        renewal_days_ago = self.expiration_date - timezone.timedelta(
            days=DAYS_BEFORE_RENEWAL
        )
        return renewal_days_ago < timezone.now() and self.status == "completed"

    # def clean(self):
    #     if self.pk:  # Check if the object is being updated
    #         original_payment = PaymentHistory.objects.filter(pk=self.pk).first()
    #         if original_payment and  original_payment.status == "completed" and self.status != "completed":
    #             raise ValidationError("Status cannot be changed from 'completed'.")
    #     super().clean()

    def save(self, *args, **kwargs):
        if self.status == "completed" and self.expiration_date is None:
            duration_days = self.duration * 30

            # Check if the user has an active subscription or free tier
            subscription_status = check_subscription_status(self.user)

            start_date = timezone.now()
            if subscription_status["free_tier_active"]:
                start_date = subscription_status["free_days_ago"]
            elif subscription_status["last_payment_active"]:
                start_date = subscription_status["last_payment"].expiration_date

            self.expiration_date = start_date + timezone.timedelta(days=duration_days)

        if self.amount is None:
            amount = self.package.price * self.duration
            self.amount = amount - self.discount if self.discount else amount

            # persistent package data
            self.package_name = self.package.name
            self.package_description = self.package.description
            self.package_price = self.package.price
            self.package_zatca_related = self.package.zatca_related

        super().save(*args, **kwargs)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.user.email
