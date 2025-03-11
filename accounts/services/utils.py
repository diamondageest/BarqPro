from django.utils import timezone
from .constants import ACCOUNT_REQUIRED_FIELDS
from django.conf import settings

FREE_PERIOD = settings.FREE_PERIOD


def are_required_fields_filled(account):
    """
    Check if all required fields are filled in the account.
    """
    return all(getattr(account, field, None) for field in ACCOUNT_REQUIRED_FIELDS)


def check_subscription_status(user):
    """
    Check if the user has an active subscription or free tier.
    """
    free_days_ago = user.date_joined + timezone.timedelta(days=FREE_PERIOD)
    free_tier_active = timezone.now() <= free_days_ago

    # the first payment not expired
    last_payment = user.subscriptions.filter(status="completed").last()
    last_payment_active = (not last_payment.is_expiry) if last_payment else None

    return {
        "free_days_ago": free_days_ago,
        "free_tier_active": free_tier_active,
        "last_payment": last_payment,
        "last_payment_active": last_payment_active,
    }
