from django.urls import path
from .views import (
    CustomerListView,
    ProductListView,
    CustomerDetailView,
    ProductDetailView,
    InvoiceListView,
    InvoiceStatusView,
    EditInvoiceCodeView,
    EditInvoiceDocumentView,
    InvoicePdfView,
)

urlpatterns = [
    path("", InvoiceListView.as_view(), name="invoice-list-create"),
    path("<int:pk>/", EditInvoiceCodeView.as_view(), name="invoice-detail"),
    path("offer/<int:pk>/", EditInvoiceDocumentView.as_view(), name="offer-detail"),
    path("customers/", CustomerListView.as_view(), name="customer-create"),
    path("customers/<int:pk>/", CustomerDetailView.as_view(), name="customer-detail"),
    path("products/", ProductListView.as_view(), name="product-create"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("status/", InvoiceStatusView.as_view(), name="invoice-status"),
    path("pdf/<int:pk>/", InvoicePdfView.as_view(), name="invoice-pdf"),
]
