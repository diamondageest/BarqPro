from django.db import models
from django.utils import timezone
import uuid
from django.db.models import Sum
from django.contrib.auth import get_user_model
from accounts.models import Account
from django.core.exceptions import ValidationError
from accounts.models import NumericLengthValidator
from django.core.validators import MinValueValidator
from decimal import Decimal
from .services.qrcode import generate_qrcode
import datetime
from .services.constants import (
    DOCUMENT_TYPES,
    INVOICE_TYPES,
    INVOICE_CODE,
    PAYMENT_METHODS,
    DISCOUNT_TYPES,
    INVOICE_STATUS,
    HISTORY_ACTION_TYPE,
)

User = get_user_model()


class Customer(models.Model):
    # NOTE: country field existed in xml structure so I add it it SA as default

    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="customers"
    )

    organization = models.CharField(
        max_length=255, help_text="Organization name in english"
    )
    tax_number = models.CharField(
        max_length=15,
        validators=[NumericLengthValidator(field_name="Tax Number", length=15)],
        null=True,
    )
    street = models.CharField(
        max_length=255, help_text="Street name in english", null=True
    )
    city = models.CharField(max_length=255, help_text="City name in english", null=True)

    # contact info
    phone = models.CharField(max_length=30)
    email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    # additional address information  ??? TODO MEED DELETE null these required
    building_number = models.CharField(
        max_length=4,
        null=True,
        validators=[NumericLengthValidator(field_name="Building Number", length=4)],
    )
    postal_zone = models.CharField(
        max_length=5,
        null=True,
        validators=[NumericLengthValidator(field_name="Postal Zone", length=5)],
    )
    district_name = models.CharField(max_length=100, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["id", "account"]),
        ]

    def __str__(self):
        return self.organization


class Product(models.Model):
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="products", db_index=True
    )
    name = models.CharField(max_length=255)
    price = models.DecimalField(
        max_digits=200,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("1.00"))],
        help_text="Price in SAR. Before VAT",
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class InvoiceCustomer(models.Model):
    # NOTE: country field existed in xml structure I add it it SA as default

    organization = models.CharField(max_length=255)
    tax_number = models.CharField(
        max_length=15,
        validators=[NumericLengthValidator(field_name="Tax Number", length=15)],
        null=True,
    )
    city = models.CharField(max_length=255, null=True)
    street = models.CharField(max_length=255, null=True)

    # contact info
    phone = models.CharField(max_length=30)
    email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    # additional address information  ??? TODO MEED DELETE null these required
    building_number = models.CharField(
        max_length=4,
        null=True,
        validators=[NumericLengthValidator(field_name="Building Number", length=4)],
    )
    postal_zone = models.CharField(
        max_length=5,
        null=True,
        validators=[NumericLengthValidator(field_name="Postal Zone", length=5)],
    )
    district_name = models.CharField(max_length=100, null=True)

    def __str__(self):
        return self.organization


class Invoice(models.Model):
    # this public invoice unique identifier and not related to Zatca
    document_type = models.CharField(
        max_length=255,
        choices=DOCUMENT_TYPES,
        default="invoice",
        db_index=True,
        help_text="Determines if this is a regular invoice or an offer price quote",
    )
    valid_until = models.DateField(
        null=True,
        blank=True,
        help_text="Date until which the offer price is valid, when the document type is an offer",
    )
    uid = models.CharField(max_length=255, null=True, db_index=True)
    invoice_type = models.CharField(
        max_length=255, choices=INVOICE_TYPES, default="simplified", db_index=True
    )
    invoice_code = models.CharField(
        max_length=255, choices=INVOICE_CODE, default="invoice", db_index=True
    )
    invoice_number = models.PositiveBigIntegerField(null=True)
    invoice_pk = models.CharField(max_length=255, null=True)

    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="invoices", db_index=True
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
        help_text="Customer is required only for standard invoice",
    )
    customer_info = models.ForeignKey(
        InvoiceCustomer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
        db_index=True,
    )  # save customer info in invoice if user edit or delete customer itself
    delivery_date = models.DateField(
        default=datetime.date.today,
    )
    payment_method = models.CharField(
        max_length=255, choices=PAYMENT_METHODS, db_index=True
    )
    qrcode = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=255, choices=INVOICE_STATUS, default="standby", db_index=True
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    # This will be fill automatically when user share the invoice with zatca
    shared_at = models.DateTimeField(null=True, blank=True, db_index=True)

    # invoice amounts
    sub_total = models.DecimalField(max_digits=500, decimal_places=2, null=True)
    vat_amount = models.DecimalField(max_digits=500, decimal_places=2, null=True)
    discount_amount = models.DecimalField(
        max_digits=500, decimal_places=2, default=Decimal("0.00")
    )
    discount_type = models.CharField(
        max_length=255,
        choices=DISCOUNT_TYPES,
        default="amount",
    )
    total_after_discount = models.DecimalField(
        max_digits=500, decimal_places=2, null=True
    )
    total_after_vat = models.DecimalField(max_digits=500, decimal_places=2, null=True)

    # This note will be fill from zatca, if invoice status is passed_with_warnings
    note = models.TextField(null=True, blank=True)

    # This will be fill automatically when user change the invoice code from invoice to credit so this invoice reference
    reference_pk = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["invoice_code", "created_at"]),
            models.Index(fields=["invoice_code", "created_at", "payment_method"]),
            models.Index(fields=["invoice_code", "created_at", "status"]),
        ]

    def __str__(self):
        return str(self.id)

    def clean(self):
        if self.invoice_type == "standard" and not self.customer:
            raise ValidationError("Customer is required for standard invoice")

        if (
            self.discount_type == "percentage"
            and self.discount_amount > 100
            and not self.id
        ):
            raise ValidationError("Discount percentage cannot be greater than 100%")

        if self.document_type == "offer" and not self.valid_until:
            raise ValidationError(
                "Valid until date is required for offer document type"
            )

        return super().clean()

    def compute_invoice_data(self):
        """
        Compute invoice amounts and save them in database
        """
        totals = self.items.aggregate(
            sub_total=Sum("sub_total"),
            total=Sum("total"),
        )

        self.sub_total = totals["sub_total"]
        if self.discount_type == "percentage":
            self.discount_amount = self.sub_total * (self.discount_amount / 100)
        self.total_after_discount = self.sub_total - self.discount_amount
        self.vat_amount = self.total_after_discount * (self.account.vat / 100)
        self.total_after_vat = self.total_after_discount + self.vat_amount
        self.qrcode = generate_qrcode(self)
        self.save()

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.customer and self.customer_info is None:
            if self.customer.tax_number:
                self.invoice_type = "standard"

            # Create a new InvoiceCustomer object and copy relevant fields from Customer
            fields_to_exclude = ["id", "account", "created_at"]
            customer_fields = {
                key.attname: getattr(self.customer, key.attname)
                for key in self.customer._meta.fields
                if key.name not in fields_to_exclude
            }
            self.customer_info, _ = InvoiceCustomer.objects.get_or_create(
                **customer_fields
            )
        if self.uid is None:
            from .services.utils import generate_invoice_uid

            self.uid = generate_invoice_uid(self.account, self.document_type)

        return super().save(*args, **kwargs)


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="items", db_index=True
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, related_name="items", null=True
    )

    # save product info in invoice item if user edit or delete product itself
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=200, decimal_places=2)

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )
    vat = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        help_text="VAT percentage",
    )
    discount = models.DecimalField(
        max_digits=200, decimal_places=2, default=Decimal("0.00")
    )

    # invoice item amounts
    sub_total = models.DecimalField(max_digits=400, decimal_places=2, null=True)
    vat_amount = models.DecimalField(max_digits=400, decimal_places=2, null=True)
    total = models.DecimalField(max_digits=400, decimal_places=2, null=True)

    def save(self, *args, **kwargs):
        if not self.name and not self.price:
            if self.invoice.account:
                self.vat = self.invoice.account.vat

            self.name = self.product.name
            self.price = self.product.price

            self.sub_total = (
                self.price * self.quantity
            )  # total without vat after discount
            self.vat_amount = self.sub_total * (self.vat / 100)  # vat amount
            self.total = self.sub_total + self.vat_amount  # total with vat and discount

        super(InvoiceItem, self).save(*args, **kwargs)

    def __str__(self):
        return f"Item #{self.pk} - {self.name}"


class InvoiceHistory(models.Model):
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="history"
    )
    action_type = models.CharField(
        max_length=255, choices=HISTORY_ACTION_TYPE, default="change_invoice_code"
    )

    # This note will be fill from zatca, if invoice status is rejected
    note = models.TextField(null=True, blank=True)

    # previous invoice data
    uid = models.CharField(max_length=255, null=True)
    invoice_code = models.CharField(max_length=255, choices=INVOICE_CODE)
    qrcode = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=255, choices=INVOICE_STATUS, default="pending")
    created_date = models.DateTimeField()
    shared_date = models.DateTimeField(null=True)

    created_at = models.DateTimeField(default=timezone.now)

    @staticmethod
    def can_share_credit_invoice(invoice):
        """
        Check if the credit invoice can be shared with Zatca
         - invoice status is passed or passed_with_warnings
         - invoice date is after last otp update
        """
        related_invoice = (
            InvoiceHistory.objects.select_related(
                "invoice", "invoice__account", "invoice__account__zatca_account"
            )
            .filter(
                invoice=invoice,
                action_type="change_invoice_code",
                status__in=["passed", "passed_with_warnings"],
            )
            .order_by("created_at")
            .first()
        )
        if related_invoice:
            last_updated = related_invoice.invoice.account.zatca_account.updated_at
            is_after_last_config = (
                related_invoice.shared_date > last_updated if last_updated else True
            )

            return is_after_last_config

        return False

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invoice #{self.invoice.pk}"
