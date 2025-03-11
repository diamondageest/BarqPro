from django.contrib import admin
from .models import (
    Invoice,
    InvoiceItem,
    Customer,
    Product,
    InvoiceCustomer,
    InvoiceHistory,
)
from django.utils import timezone

admin.site.register(InvoiceCustomer)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        "account",
        "organization",
        "phone",
    ]
    search_fields = ["account__user__email"]
    readonly_fields = ["created_at"]


@admin.register(Product)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["account", "name"]
    search_fields = ["account__user__email"]
    readonly_fields = ["created_at"]


@admin.register(InvoiceHistory)
class InvoiceHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "uid",
        "action_type",
        "status",
        "created_date",
        "shared_date",
        "created_at",
    ]
    list_filter = ["created_at", "action_type"]
    search_fields = ["invoice__account__user__email", "uid"]
    readonly_fields = ["created_at"]

    def get_readonly_fields(self, request, obj=None):
        # If the invoice is already created, make all fields read-only
        if obj and obj.pk:
            return [field.name for field in self.model._meta.fields]

        return super().get_readonly_fields(request, obj)


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    exclude = ("discount",)
    readonly_fields = (
        "name",
        "price",
        "vat",
        "sub_total",
        "vat_amount",
        "total",
        # "total_after_discount",
    )

    def get_readonly_fields(self, request, obj=None):
        # If the invoice is already created, make all fields read-only
        if obj and obj.pk:
            return [field.name for field in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)

    def has_add_permission(self, request, obj=None):
        # Prevent adding new items once the invoice is created
        if obj and obj.pk:
            return False
        return super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # This prevents users from deleting invoices as well
        return False


class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "uid",
        "document_type",
        "account",
        "invoice_type",
        "invoice_code",
        "total_after_vat",
        "status",
        "created_at",
    )
    inlines = [InvoiceItemInline]
    readonly_fields = (
        "uid",
        "invoice_type",
        "invoice_pk",
        "invoice_number",
        "customer_info",
        "sub_total",
        "vat_amount",
        "total_after_discount",
        "total_after_vat",
        "qrcode",
        "status",
        "delivery_date",
        "created_at",
        "shared_at",
        "reference_pk",
        "note",
    )
    list_filter = ("invoice_type", "invoice_code", "status", "created_at")
    search_fields = ["uid", "account__user__email"]

    def get_search_results(self, request, queryset, search_term):
        # Split the search term into uid and email
        uid, email = (
            search_term.split(" ", 1) if " " in search_term else (search_term, "")
        )
        # Perform the search using Q objects
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )
        if uid and email:
            queryset |= self.model.objects.filter(
                uid__icontains=uid, account__user__email__icontains=email
            )

        return queryset, use_distinct

    # def has_delete_permission(self, request, obj=None):
    #     # This prevents users from deleting invoices as well
    #     return False

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if not change:  # Only calculate when creating a the Invoice
            invoice = form.instance
            invoice.compute_invoice_data()
            discount_amount = invoice.discount_amount
            if discount_amount > 0:
                invoice_items = invoice.items.all()
                item_discount = discount_amount / invoice_items.count()
                for item in invoice_items:
                    item.discount = item_discount
                    item.save()

    # def save_model(self, request, obj, form, change):
    #     # Calculate the discount amount and set it for each InvoiceItem

    #     if obj.invoice_code == "credit":
    #         obj.created_at = timezone.now()
    #     super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        # If the invoice is already created, make all fields read-only
        if obj and obj.pk:
            return [
                field.name
                for field in self.model._meta.fields
                # if field.name != "status"
            ]

        return super().get_readonly_fields(request, obj)

    change_form_template = "admin/invoice_change_form.html"

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}

        # Retrieve the invoice_code for the current invoice
        invoice = Invoice.objects.get(pk=object_id)

        # Check if the user has a ZATCA account
        is_accepted_account, account_note = invoice.account
        extra_context["invoice_id"] = object_id

        has_zatca_account = request.user
        is_invoice_passed = invoice.status in ["passed", "passed_with_warnings"]
        allow_change = is_invoice_passed if has_zatca_account else True

        extra_context["change_to_credit"] = (
            allow_change and invoice.invoice_code == "invoice"
        )
        extra_context["share_with_zatca"] = (
            invoice.status
            in [
                "standby",
                "rejected",
                "error",
            ]
            and invoice.document_type == "invoice"
        )

        extra_context["invoice_history"] = invoice.history.all().count()
        # extra_context["pdf_available"] = invoice.status in ["passed", "passed_with_warnings"]
        extra_context["pdf_available"] = True

        extra_context["is_accepted_account"] = is_accepted_account
        extra_context["account_note"] = account_note

        return super().change_view(
            request, object_id, form_url=form_url, extra_context=extra_context
        )


admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(InvoiceItem)
