from __future__ import annotations

from datetime import date, datetime

from django import template
from django.utils import timezone


register = template.Library()

@register.filter
def has_role(user, role_name: str) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return user.groups.filter(name=role_name).exists()


@register.filter
def has_any_role(user, role_names: str) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    names = [name.strip() for name in (role_names or "").split(",") if name.strip()]
    if not names:
        return False
    return user.groups.filter(name__in=names).exists()


@register.filter
def date_or_datetime(value, arg="date"):
    if not value:
        return "-"

    if isinstance(value, datetime):
        current = timezone.localtime(value) if timezone.is_aware(value) else value
        if arg == "datetime":
            return current.strftime("%d/%m/%Y %I:%M %p")
        return current.strftime("%d/%m/%Y")

    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")

    return value
