# Generated by Django 4.2.5 on 2023-12-11 01:50

import accounts.services.validators
from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Account",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "organization",
                    models.CharField(
                        help_text="Organization name in english",
                        max_length=255,
                        null=True,
                    ),
                ),
                ("register_number", models.CharField(max_length=255, null=True)),
                (
                    "tax_number",
                    models.CharField(
                        max_length=15,
                        null=True,
                        validators=[
                            accounts.services.validators.NumericLengthValidator(
                                field_name="Tax Number", length=15
                            )
                        ],
                    ),
                ),
                (
                    "country",
                    models.CharField(
                        default="SA", help_text="Country code", max_length=3, null=True
                    ),
                ),
                (
                    "city",
                    models.CharField(
                        help_text="City name in english", max_length=255, null=True
                    ),
                ),
                (
                    "street",
                    models.CharField(
                        help_text="Street name in english", max_length=255, null=True
                    ),
                ),
                ("phone", models.CharField(max_length=30, null=True)),
                ("taxable", models.BooleanField(default=True)),
                (
                    "vat",
                    models.DecimalField(
                        decimal_places=1,
                        default=Decimal("15.0"),
                        help_text="VAT percentage",
                        max_digits=3,
                        validators=[accounts.services.validators.VatValidator()],
                    ),
                ),
                ("logo", models.ImageField(blank=True, null=True, upload_to="logos/")),
            ],
        ),
        migrations.CreateModel(
            name="Package",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(default="")),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Price in SAR per month",
                        max_digits=10,
                    ),
                ),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PaymentHistory",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=14, null=True
                    ),
                ),
                ("duration", models.IntegerField(help_text="Duration in months")),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "pending"), ("completed", "completed")],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("expiration_date", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "package_name",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("package_description", models.TextField(blank=True, null=True)),
                (
                    "package_price",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                (
                    "package",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="subscriptions",
                        to="accounts.package",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
    ]
