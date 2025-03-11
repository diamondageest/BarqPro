from rest_framework import generics, status
from .models import Customer, Product, Invoice
from .serializers import (
    CustomerSerializer,
    ProductSerializer,
    InvoiceCreateSerializer,
    InvoiceCodeSerializer,
    InvoiceDocumentSerializer,
)
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Q
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from .services.filters import InvoiceFilter
from datetime import timedelta
from django.shortcuts import render
from .services.qrcode import create_qrcode_image
from django.views import View
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import (
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseForbidden,
)


User = get_user_model()


class AccountRelatedMixin:
    """
    Filter objects by account and set account field when creating an object
    """

    model = None

    def get_queryset(self):
        if self.model is None:
            raise NotImplementedError(
                "You must define the 'model' attribute in your subclass."
            )
        return self.model.objects.filter(account=self.request.user.account)

    def perform_create(self, serializer):
        if self.model is None:
            raise NotImplementedError(
                "You must define the 'model' attribute in your subclass."
            )
        serializer.save(account=self.request.user.account)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class CustomerListView(AccountRelatedMixin, generics.ListCreateAPIView):
    serializer_class = CustomerSerializer
    model = Customer


class CustomerDetailView(AccountRelatedMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomerSerializer
    model = Customer


class ProductListView(AccountRelatedMixin, generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    model = Product


class ProductDetailView(AccountRelatedMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    model = Product


class InvoiceListView(AccountRelatedMixin, generics.ListCreateAPIView):
    serializer_class = InvoiceCreateSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = InvoiceFilter
    model = Invoice


class EditInvoiceCodeView(AccountRelatedMixin, generics.UpdateAPIView):
    serializer_class = InvoiceCodeSerializer
    model = Invoice

    def get_queryset(self):
        return super().get_queryset().filter(document_type="invoice")


class EditInvoiceDocumentView(AccountRelatedMixin, generics.UpdateAPIView):
    serializer_class = InvoiceDocumentSerializer
    model = Invoice

    def get_queryset(self):
        return super().get_queryset().filter(document_type="offer")


class InvoiceStatusView(APIView):
    """
    Get invoice status statistics in a day and a month
    """

    def get(self, request):
        account = request.user.account
        today = timezone.now().date()
        date_30_days_ago = today - timedelta(days=30)

        queryset = Invoice.objects.filter(
            account=account, document_type="invoice"
        ).values("invoice_code", "created_at")
        queryset = queryset.aggregate(
            total_in_day=Sum(
                "total_after_vat",
                filter=Q(created_at__date=today, invoice_code="invoice"),
            ),
            total_in_month=Sum(
                "total_after_vat",
                filter=Q(
                    created_at__date__gte=date_30_days_ago, invoice_code="invoice"
                ),
            ),
            credit_total_in_day=Sum(
                "total_after_vat",
                filter=Q(created_at__date=today, invoice_code="credit"),
            ),
            credit_total_in_month=Sum(
                "total_after_vat",
                filter=Q(created_at__date__gte=date_30_days_ago, invoice_code="credit"),
            ),
        )

        stats = {
            "invoices_in_day": queryset["total_in_day"] or 0,
            "invoices_in_month": queryset["total_in_month"] or 0,
            "credit_in_day": queryset["credit_total_in_day"] or 0,
            "credit_in_month": queryset["credit_total_in_month"] or 0,
        }

        return Response(stats, status=status.HTTP_200_OK)


class InvoicePdfView(View):
    """
    Get invoice pdf file by invoice id and access token
    """

    def is_admin_user(self, user):
        return (user.is_superuser or user.is_staff) and user.is_authenticated

    def get(self, request, pk):
        access_token = request.GET.get("token")
        is_admin = self.is_admin_user(request.user)

        if not is_admin:
            if not access_token:
                return HttpResponseBadRequest()

            try:
                payload = jwt.decode(
                    access_token, settings.SECRET_KEY, algorithms=["HS256"]
                )
                user_id = payload["user_id"]
            except jwt.ExpiredSignatureError:
                return HttpResponseBadRequest("Access token has expired")
            except jwt.DecodeError:
                return HttpResponseBadRequest("Invalid access token")

        try:
            user = User.objects.get(id=user_id) if not is_admin else None
            invoice = Invoice.objects.get(id=pk)

            # check invoice status
            # if invoice.status not in ["passed", "passed_with_warnings"]:
            #     return HttpResponseBadRequest("Invalid pdf for non-passed invoice to ZATCA")

            # Check if the user is authorized to access this invoice
            if is_admin or user == invoice.account.user:
                qrcode = create_qrcode_image(invoice.qrcode)
                return render(
                    request,
                    "invoices/pdf_mold.html",
                    {"invoice": invoice, "qrcode": qrcode},
                )
            else:
                return HttpResponseForbidden()
        except Invoice.DoesNotExist:
            return HttpResponseNotFound("Invoice not found")
        except User.DoesNotExist:
            return HttpResponseNotFound("User not found")
