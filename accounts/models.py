from __future__ import annotations

from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    signature_file = models.FileField(upload_to="signatures/", blank=True, null=True)

    def __str__(self) -> str:
        return f"Profile: {self.user.username}"

