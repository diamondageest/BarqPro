from rest_framework import permissions
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from django.conf import settings

FREE_PERIOD = settings.FREE_PERIOD
DAYS_BEFORE_RENEWAL = settings.DAYS_BEFORE_RENEWAL


class IsEmailVerified(permissions.BasePermission):
    """
    Custom permission to check if a user's email is verified.
    """

    message = "Your email is not verified. Please verify your email."

    def has_permission(self, request, view):
        return request.user.email_verified


class IsAccountCompleted(permissions.BasePermission):
    """
    Custom permission to check if a user's account is completed.
    """

    message = "Your account is not completed. Please complete your account setup."

    def has_permission(self, request, view):
        # Check if the user's account is completed
        return request.user.profile_completed


class IsSubscriptionActive(permissions.BasePermission):
    """
    Custom permission to check if a user's subscription is active.
    """

    def is_active_before_pending(self, user):
        """
        Check if the last completed payment is active before the last pending payment.
        """

        last_completed_payment = user.subscriptions.filter(status="completed").last()
        return (
            (not last_completed_payment.is_expiry) if last_completed_payment else None
        )

    def has_permission(self, request, view):
        user = request.user

        # check last created payment
        last_payment = user.subscriptions.last()

        free_days_ago = user.date_joined + timezone.timedelta(days=FREE_PERIOD)
        free_tier_active = timezone.now() <= free_days_ago

        if last_payment is None or free_tier_active:
            if free_tier_active:
                return True
            raise PermissionDenied("Your free trial period has ended.")

        elif last_payment.status == "pending":
            if self.is_active_before_pending(user):
                return True

            raise PermissionDenied(
                "Your subscription package is pending. Wait to complete your payment"
            )

        elif last_payment.is_expiry:
            raise PermissionDenied(
                "Your last subscription package has expired. Please renew your subscription package"
            )
        elif last_payment.status == "not_active":
            raise PermissionDenied(
                "Your last subscription package is not active. Please contact support for assistance."
            )
        else:
            return True


class CanCreatePayment(permissions.BasePermission):
    """
    Custom permission to check if a user can create a payment.
    """

    def has_permission(self, request, view):
        if request.method == "POST":
            user = request.user
            last_payment = user.subscriptions.last()

            # Check if the user's free trial period is over
            if last_payment is None:
                return True

            if last_payment.status == "pending":
                raise PermissionDenied(
                    "Your subscription package is pending. Wait to complete your payment"
                )
            elif last_payment.can_subscribe:
                return True

            raise PermissionDenied(
                f"You can only subscribe again within the last {DAYS_BEFORE_RENEWAL} days of your active subscription."
            )
        else:
            return True
