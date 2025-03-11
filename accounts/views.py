from rest_framework import generics, status, permissions
from .serializers import AccountSerializer, PaymentSerializer, PackageSerializer
from rest_framework.response import Response
from .models import PaymentHistory
from accounts.services.permissions import (
    IsEmailVerified,
    IsAccountCompleted,
    CanCreatePayment,
)
from rest_framework.parsers import FormParser, MultiPartParser


class AccountDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve and update a user's business account details
    Permissions: IsAuthenticated
    """

    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]
    parser_classes = (
        FormParser,
        MultiPartParser,
    )
    allowed_methods = ["GET", "PUT"]

    def get_object(self):
        return self.request.user.account


class PaymentListAPIView(generics.ListCreateAPIView):
    """
    List all user's payment history
    """

    serializer_class = PaymentSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsEmailVerified,
        IsAccountCompleted,
        CanCreatePayment,
    ]

    def get_queryset(self):
        return PaymentHistory.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PackageListAPIView(generics.ListAPIView):
    """
    List all Packages that created by admin in admin portal
    """

    serializer_class = PackageSerializer
    queryset = PackageSerializer.Meta.model.objects.all()
    permission_classes = [
        permissions.IsAuthenticated,
        IsEmailVerified,
        IsAccountCompleted,
    ]
