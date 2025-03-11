from accounts.models import Account
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .utils import are_required_fields_filled

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_account(sender, instance, created, **kwargs):
    if created:
        Account.objects.create(user=instance)


@receiver(post_save, sender=Account)
def update_profile_completed(sender, instance: Account, created, **kwargs):
    if not created and not instance.user.profile_completed:
        if are_required_fields_filled(instance):
            instance.user.profile_completed = True
            instance.user.save(update_fields=["profile_completed"])
