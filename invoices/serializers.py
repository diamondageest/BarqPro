from rest_framework import serializers
from .models import Customer, Product, Invoice, InvoiceItem
from decimal import Decimal
from django.utils import timezone
from .services.constants import CUSTOMER_INFO_REQUIRED, CUSTOMER_ZATCA_INFO_REQUIRED
from invoices.services.utils import create_invoice_history


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "organization",
            "tax_number",
            "street",
            "city",
            "email",
            "phone",
            "building_number",
            "postal_zone",
            "district_name",
        ]
        read_only_fields = [
            "id",
        ]

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        tax_number = validated_data.get("tax_number")

        # Check if the customer has a tax number
        if tax_number:
            for item in CUSTOMER_INFO_REQUIRED:
                if not validated_data.get(item):
                    raise serializers.ValidationError(
                        {
                            f"{item}": f"{item} field is required for customer with tax number"
                        }
                    )

            # check if user have zatca account
            user = self.context["request"].user
            has_zatca_account = user
            if has_zatca_account:
                for item in CUSTOMER_ZATCA_INFO_REQUIRED:
                    if not validated_data.get(item):
                        raise serializers.ValidationError(
                            {
                                f"{item}": f"{item} field is required for customer with tax number when you have a Zatca account"
                            }
                        )

        return validated_data


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        exclude = ["account", "created_at"]


class InvoiceItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), required=True, write_only=True
    )

    class Meta:
        model = InvoiceItem
        fields = [
            "product",
            "name",
            "price",
            "quantity",
            "vat",
            "sub_total",
            "vat_amount",
            "total",
        ]
        read_only_fields = [
            "name",
            "price",
            "vat",
            "sub_total",
            "vat_amount",
            "total",
        ]


class InvoiceCreateSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_type",
            "invoice_code",
            "payment_method",
            "items",
            "customer",
            "sub_total",
            "vat_amount",
            "discount_amount",
            "discount_type",
            "total_after_discount",
            "total_after_vat",
            "delivery_date",
            "created_at",
            "qrcode",
            "status",
            "uid",
            "document_type",
            "valid_until",
        ]
        read_only_fields = [
            "id",
            "invoice_type",
            "invoice_code",
            "uid",
            "status",
            "sub_total",
            "vat_amount",
            "total_after_discount",
            "total_after_vat",
            "delivery_date",
            "created_at",
            "qrcode",
        ]
        write_only_fields = [
            "discount_type",
        ]

    def validate(self, data):
        validated_date = super().validate(data)
        # Check if document type is offer and valid_until is provided
        document_type = validated_date.get("document_type")
        valid_until = validated_date.get("valid_until")

        if document_type == "offer" and not valid_until:
            raise serializers.ValidationError(
                {"valid_until": "Valid until date is required for offer documents"}
            )

        # Validate that valid_until is a future date if provided
        if valid_until and valid_until <= timezone.now().date():
            raise serializers.ValidationError(
                {"valid_until": "Valid until date must be a future date"}
            )

        return validated_date

    def validate_discount_type(self, value):
        discount_value = self.initial_data.get("discount_amount")
        if not discount_value:
            raise serializers.ValidationError(
                {
                    "discount_value": "if you submit discount_type you must submit discount_value"
                }
            )
        return value

    def validate_discount_value(self, value):
        discount_type = self.initial_data.get("discount_type")
        if discount_type == "percentage" and Decimal(value) > 100:
            raise serializers.ValidationError(
                {"discount_value": "Discount percentage cannot be greater than 100%"}
            )

        return value

    def validate_customer(self, item):
        user = self.context["request"].user
        try:
            Customer.objects.get(id=item.id, account__user=user)
        except Customer.DoesNotExist:
            raise serializers.ValidationError({"customer": "Invalid customer provided"})

        return item

    def check_items(self, value):
        """
        Check if the items are valid and compute the invoice data (sub total, vat amount, etc.)
        """
        user = self.context["request"].user
        discount = self.initial_data.get("discount_amount", 0)
        discount_type = self.initial_data.get("discount_amount", "amount")
        validated_items = []
        sub_total = 0

        for item_data in value:
            try:
                product = Product.objects.get(
                    id=item_data["product"].id, account__user=user
                )
            except Product.DoesNotExist:
                raise serializers.ValidationError("Invalid product provided")

            validated_items.append(
                {
                    "product": product,
                    "quantity": item_data["quantity"],
                }
            )
            sub_total += product.price * item_data["quantity"]

        # Check if the discount type is percentage
        if discount_type == "percentage":
            discount = sub_total * (Decimal(discount) / 100)

        # Check if the discount is greater than the sub total
        if Decimal(discount) > sub_total:
            raise serializers.ValidationError(
                {
                    "discount_amount": "Discount cannot be greater than sub total of the invoice"
                }
            )

        return validated_items

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        discount_amount = validated_data.get("discount_amount")
        # Check if the items are valid
        self.check_items(items_data)

        if discount_amount:
            item_discount = discount_amount / len(items_data)
        else:
            item_discount = 0

        invoice = Invoice.objects.create(**validated_data)

        for item_data in items_data:
            InvoiceItem.objects.create(
                invoice=invoice, **item_data, discount=item_discount
            )
        invoice.compute_invoice_data()
        return invoice

    def get_items(self, obj):
        """
        Retrieve invoice items from the InvoiceItem model
        """
        items = InvoiceItem.objects.filter(invoice=obj)
        return InvoiceItemSerializer(items, many=True).data

    def retrieve_customer_info(self, obj):
        """
        Retrieve customer info from the InvoiceCustomer model
        """
        if obj.customer_info:
            customer = obj.customer_info
            data = CustomerSerializer(customer).data
            data.pop("id")
            return data
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.invoice_type == "simplified":
            data.pop("delivery_date")
        if instance.customer_info:
            data["customer"] = self.retrieve_customer_info(instance)
        else:
            data.pop("customer")

        return data


class InvoiceCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ["invoice_code"]

    def validate_invoice_code(self, invoice_code):
        if not invoice_code:
            raise serializers.ValidationError("Invoice Code is required")

        if invoice_code != "credit":
            raise serializers.ValidationError(
                "Invoice Code must be 'credit' because this keyword is related to refunds"
            )

        return invoice_code

    def validate(self, data):
        instance = self.instance
        invoice_code = data.get("invoice_code")

        if invoice_code == instance.invoice_code:
            raise serializers.ValidationError("This invoice is already credit.")

        # Check if the user has a Zatca account and the invoice is passed
        has_zatca_account = self.context["request"].user
        is_invoice_passed = instance.status in ["passed", "passed_with_warnings"]

        if has_zatca_account and not is_invoice_passed:
            raise serializers.ValidationError(
                "This invoice is not passed. Share the invoice with Zatca before change it credit"
            )

        return data

    def update(self, instance: Invoice, validated_data):
        # create a history record
        create_invoice_history(instance, action_type="change_invoice_code")

        # update the invoice code
        # instance.invoice_code = validated_data["invoice_code"]
        instance.invoice_code = "credit"
        instance.reference_pk = instance.invoice_pk
        instance.created_at = timezone.now()
        instance.status = "standby"
        instance.note = None
        instance.invoice_number = None
        instance.invoice_pk = None
        instance.uid = instance.uid.replace("IN", "RE")
        instance.save(
            update_fields=[
                "invoice_code",
                "reference_pk",
                "created_at",
                "status",
                "note",
                "invoice_number",
                "invoice_pk",
                "uid",
            ]
        )
        return instance

    def to_representation(self, instance):
        return {
            "status": f"The Invoice Code has been updated to {instance.invoice_code}"
        }


class InvoiceDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ["document_type"]

    def validate_document_type(self, document_type):
        if not document_type:
            raise serializers.ValidationError("Invoice Document is required")
        elif document_type != "invoice":
            raise serializers.ValidationError(
                "Invoice Document must be 'invoice' because this keyword is related to charge offer document to invoice document"
            )

        return document_type

    def update(self, instance: Invoice, validated_data):
        # Check if the offer document has expired
        if instance.valid_until and instance.valid_until < timezone.now().date():
            raise serializers.ValidationError(
                {"valid_until": "The offer document has expired"}
            )

        # create a history record
        create_invoice_history(instance, action_type="change_document_type")

        # update the invoice document
        instance.document_type = "invoice"
        instance.uid = instance.uid.replace("OF", "IN")
        instance.created_at = timezone.now()
        instance.save(update_fields=["document_type", "uid", "created_at"])
        return instance
