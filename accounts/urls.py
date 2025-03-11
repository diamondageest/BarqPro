from django.urls import path
from . import views

urlpatterns = [
    path("", views.AccountDetailView.as_view(), name="account-create"),
    path("payments/", views.PaymentListAPIView.as_view(), name="payment-list"),
    path("packages/", views.PackageListAPIView.as_view(), name="package-list"),
]
