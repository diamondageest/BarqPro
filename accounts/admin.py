from django.contrib import admin
from .models import Account, Package, PaymentHistory


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["user", "organization", "taxable", "phone"]
    search_fields = ["user__email"]
    list_filter = ["taxable"]


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "created_at"]
    readonly_fields = ["created_at"]


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "package_name",
        "status",
        "amount",
        "is_expiry_field",
        "expiration_date",
        "created_at",
    ]
    list_filter = ["status"]
    search_fields = ["user__email", "user__account__phone"]
    readonly_fields = [
        "user_organization_name",
        "user_email",
        "user_phone",
        "package_name",
        "package_description",
        "package_price",
        "package_zatca_related",
        "amount",
        "created_at",
        "expiration_date",
        "is_expiry_field",
    ]
    fieldsets = (
        (
            "User Info",
            {
                "fields": (
                    "user",
                    "user_organization_name",
                    "user_email",
                    "user_phone",
                )
            },
        ),
        (
            "Payment Info",
            {
                "fields": (
                    "package",
                    "package_name",
                    "package_description",
                    "package_price",
                    "package_zatca_related",
                )
            },
        ),
        (
            "Payment Info",
            {
                "fields": (
                    "status",
                    "duration",
                    "amount",
                    "discount",
                    "note",
                    "created_at",
                    "expiration_date",
                    "is_expiry_field",
                )
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        read_only_fields = super().get_readonly_fields(request, obj)
        # If the invoice is already created, make all fields read-only
        if obj and obj.pk:
            return read_only_fields + ["package", "user", "duration", "discount"]

        return read_only_fields

    def user_organization_name(self, obj):
        return obj.user.account.organization

    user_organization_name.short_description = "User Organization Name"

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "User Email"

    def user_phone(self, obj):
        return obj.user.account.phone

    user_phone.short_description = "User Phone"

    def is_expiry_field(self, obj):
        return obj.is_expiry

    is_expiry_field.boolean = True  # Display as a boolean field
    is_expiry_field.short_description = "Is Expired"  # Custom column header
