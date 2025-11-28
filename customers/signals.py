# customers/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from accounts.models import UserRoles
from .models import CustomerProfile


User = settings.AUTH_USER_MODEL


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_customer_profile(sender, instance, created, **kwargs):
    # Only auto-create for customer role
    if created and getattr(instance, "role", None) == UserRoles.CUSTOMER:
        CustomerProfile.objects.get_or_create(user=instance)
