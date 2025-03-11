from rest_framework import serializers
from .models import Account, PaymentHistory, Package
from .services.constants import ACCOUNT_REQUIRED_FIELDS
from django.conf import settings

FREE_PERIOD = settings.FREE_PERIOD


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            "organization",
            "register_number",
            "tax_number",
            # "country",
            "city",
            "street",
            "phone",
            "taxable",
            "logo",
            "vat",
        ]
        read_only_fields = [
            "vat",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name in ACCOUNT_REQUIRED_FIELDS:
                field.required = True
            elif field_name == "taxable":
                field.required = True
            else:
                field.required = False

    def validate_logo(self, value):
        # Check if the logo file size exceeds the maximum allowed size (in bytes)
        max_logo_size = 1024 * 1024  # 1 MB
        if value and value.size > max_logo_size:
            raise serializers.ValidationError(
                "Logo size exceeds the maximum allowed size (1 MB)."
            )

        return value

    def to_representation(self, instance: Account):
        data = super().to_representation(instance)
        data["current_subscription"] = instance.user.current_subscription
        (
            data["has_zatca_account"],
            data["zatca_account_status"],
        ) = instance.get_zatca_account()
        return data


class PaymentSerializer(serializers.ModelSerializer):
    package = serializers.PrimaryKeyRelatedField(
        queryset=Package.objects.all(), required=True, write_only=True
    )

    class Meta:
        model = PaymentHistory
        exclude = (
            "id",
            "user",
            "package_name",
            "package_description",
            "package_price",
            "package_zatca_related",
            "note",
        )
        read_only_fields = [
            "amount",
            "status",
            "payment_id",
            "transaction_id",
            "expiration_date",
            "created_at",
        ]

    def to_representation(self, instance: PaymentHistory):
        data = super().to_representation(instance)
        data["package"] = {
            "name": instance.package_name,
            "description": instance.package_description,
            "price": instance.package_price,
        }
        return data


class FreeTierSerializer(serializers.Serializer):
    expiration_date = serializers.DateTimeField()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["package"] = {
            "name": "free",
            "description": f"free package for {FREE_PERIOD} days",
            "price": 0,
        }
        return data


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = "__all__"
