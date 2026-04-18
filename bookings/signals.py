from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .roles import sync_role_permissions


@receiver(post_migrate)
def ensure_default_roles(sender, **kwargs):
    sync_role_permissions(sync_staff_membership=True)
