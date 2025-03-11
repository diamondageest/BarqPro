import django_filters
from django import forms
from invoices.models import Invoice
from invoices.services.constants import DOCUMENT_TYPES


class InvoiceFilter(django_filters.FilterSet):
    """
    Filter invoices by invoice code and date range.
    Default document_type is always 'invoice' unless explicitly specified otherwise.
    """

    from_date = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__gte",
        label="From Date",
        widget=forms.widgets.DateInput(attrs={"type": "date"}),
    )
    to_date = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__lte",
        label="To Date",
        widget=forms.widgets.DateInput(attrs={"type": "date"}),
    )

    customer_phone = django_filters.CharFilter(
        field_name="customer_info__phone",
        lookup_expr="icontains",
        label="Customer Phone",
    )
    uid = django_filters.CharFilter(field_name="uid", lookup_expr="iexact", label="UID")

    document_type = django_filters.ChoiceFilter(
        choices=DOCUMENT_TYPES,
        empty_label=None,  # Remove empty choice
        initial="invoice",
    )

    valid_until = django_filters.DateFilter(
        field_name="valid_until",
        lookup_expr="date",
        label="Valid Until",
        widget=forms.widgets.DateInput(attrs={"type": "date"}),
    )

    class Meta:
        model = Invoice
        fields = [
            "invoice_code",
            "from_date",
            "to_date",
            "payment_method",
            "customer_phone",
            "status",
            "uid",
            "document_type",
            "valid_until",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Always ensure data is mutable
        if hasattr(self, "data") and not self.data:
            self.data = {"document_type": "invoice"}
        elif hasattr(self, "data"):
            self.data = self.data.copy()
            # Set document_type to 'invoice' if it's empty or not provided
            if not self.data.get("document_type"):
                self.data["document_type"] = "invoice"

        # Hide valid_until for non-offer documents
        if self.data.get("document_type") != "offer":
            self.form.fields["valid_until"].widget = forms.HiddenInput()

    @property
    def qs(self):
        """Override queryset property to ensure default document_type filter"""
        queryset = super().qs

        # If no document_type filter is active, filter by invoice
        if not self.form.cleaned_data.get("document_type"):
            queryset = queryset.filter(document_type="invoice")

        return queryset
