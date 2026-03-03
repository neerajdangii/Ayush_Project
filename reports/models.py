from __future__ import annotations

from django.conf import settings
from django.db import models

from bookings.models import Booking


class Report(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        MANAGER_APPROVED = "manager_approved", "Approved by Manager"
        INCHARGE_APPROVED = "incharge_approved", "Approved by Incharge"

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="report")
    analysis_end_date = models.DateField(null=True, blank=True)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="managed_reports",
        null=True,
        blank=True,
    )
    manager_name = models.CharField(max_length=255, blank=True)
    manager_signature = models.CharField(max_length=255, blank=True)
    incharge = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="incharge_reports",
        null=True,
        blank=True,
    )
    incharge_name = models.CharField(max_length=255, blank=True)
    incharge_signature = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.DRAFT)
    ceo_content = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reports",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def certificate_no(self) -> str:
        booking_type = "REGULATORY" if self.booking.booking_type == Booking.BookingType.REGULATORY else "GENERAL"
        reg_tail = self.booking.sample_reg_no.replace("ARL/", "")
        return f"ARL/{booking_type}/{reg_tail}"

    @property
    def test_names(self) -> str:
        return ", ".join(self.booking.test_to_be_performed.values_list("name", flat=True))

    def approve_by_manager(self, manager_user, incharge_user=None):
        self.manager = manager_user
        self.manager_name = manager_user.get_full_name() or manager_user.username
        self.manager_signature = "Digitally Signed"
        self.incharge = incharge_user
        if incharge_user:
            self.incharge_name = incharge_user.get_full_name() or incharge_user.username
        elif not self.incharge_name:
            self.incharge_name = "Incharge"
        self.incharge_signature = "Digital Sign"
        self.status = self.Status.INCHARGE_APPROVED
        self.save(
            update_fields=[
                "manager",
                "manager_name",
                "manager_signature",
                "incharge",
                "incharge_name",
                "incharge_signature",
                "status",
                "updated_at",
            ]
        )

    def __str__(self) -> str:
        return f"Report - {self.booking.sample_reg_no}"
