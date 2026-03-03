from __future__ import annotations

from django.conf import settings
from django.db import IntegrityError, models
from django.db.models import Max
from django.utils import timezone


class ActiveMasterModel(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class CustomerMaster(ActiveMasterModel):
    pass


class SubmitterMaster(ActiveMasterModel):
    pass


class ManufacturerMaster(ActiveMasterModel):
    pass


class SampleNameMaster(ActiveMasterModel):
    pass


class TestMaster(ActiveMasterModel):
    pass


class ProtocolMaster(ActiveMasterModel):
    pass


class UOMMaster(ActiveMasterModel):
    pass


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"

    class SampleType(models.TextChoices):
        API = "API", "API"
        FG = "FG", "FG"
        FOOD = "Food", "Food"
        RM = "RM", "RM"
        STABILITY = "Stability", "Stability"

    class BookingType(models.TextChoices):
        REGULATORY = "regulatory", "Regulatory"
        GENERAL = "general", "General"

    booking_date = models.DateField(default=timezone.now)
    letter_date = models.DateField(null=True, blank=True)
    sampling_upto = models.DateField(null=True, blank=True)
    sample_receipt_date = models.DateField(null=True, blank=True)
    customer = models.ForeignKey(
        CustomerMaster, on_delete=models.PROTECT, related_name="bookings", null=True, blank=True
    )
    submitter = models.ForeignKey(
        SubmitterMaster, on_delete=models.PROTECT, related_name="bookings", null=True, blank=True
    )
    manufacturer = models.ForeignKey(
        ManufacturerMaster, on_delete=models.PROTECT, related_name="bookings", null=True, blank=True
    )
    sample_name = models.ForeignKey(
        SampleNameMaster, on_delete=models.PROTECT, related_name="bookings", null=True, blank=True
    )
    sample_type = models.CharField(max_length=20, choices=SampleType.choices, blank=True)
    test_to_be_performed = models.ManyToManyField(TestMaster, related_name="bookings", blank=True)
    protocol = models.ForeignKey(
        ProtocolMaster, on_delete=models.PROTECT, related_name="bookings", null=True, blank=True
    )
    uom = models.ForeignKey(UOMMaster, on_delete=models.PROTECT, related_name="bookings", null=True, blank=True)
    booking_type = models.CharField(max_length=20, choices=BookingType.choices, default=BookingType.GENERAL)
    sample_reg_no = models.CharField(max_length=32, unique=True, editable=False, null=True, blank=True)
    sample_qty = models.CharField(max_length=100, blank=True)
    sample_location = models.CharField(max_length=255, blank=True)
    packaging_mode = models.CharField(max_length=255, blank=True)
    sample_condition = models.CharField(max_length=255, blank=True)
    batch_no = models.CharField(max_length=100, blank=True)
    batch_size = models.CharField(max_length=100, blank=True)
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_retest_date = models.DateField(null=True, blank=True)
    collected_by_name = models.CharField(max_length=255, blank=True)
    sampling_procedure = models.CharField(max_length=255, blank=True)
    analysis_start_date = models.DateField(null=True, blank=True)
    analysis_end_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approved_bookings",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def booking_type_code(self) -> str:
        return "REG" if self.booking_type == self.BookingType.REGULATORY else "GEN"

    @classmethod
    def _next_sequence(cls, booking_date, booking_type):
        year = booking_date.year
        prefix = f"ARL/{year}/{ 'REG' if booking_type == cls.BookingType.REGULATORY else 'GEN' }/"
        max_reg = (
            cls.objects.filter(sample_reg_no__startswith=prefix)
            .aggregate(max_reg=Max("sample_reg_no"))
            .get("max_reg")
        )
        if not max_reg:
            return 1
        try:
            return int(max_reg.rsplit("/", 1)[-1]) + 1
        except (TypeError, ValueError):
            return 1

    def generate_sample_reg_no(self) -> str:
        sequence = self._next_sequence(self.booking_date, self.booking_type)
        return f"ARL/{self.booking_date.year}/{self.booking_type_code}/{sequence:04d}"

    def save(self, *args, **kwargs):
        if self.sample_reg_no:
            super().save(*args, **kwargs)
            return

        for _ in range(3):
            self.sample_reg_no = self.generate_sample_reg_no()
            try:
                super().save(*args, **kwargs)
                return
            except IntegrityError:
                self.sample_reg_no = None
                continue
        raise IntegrityError("Unable to generate unique sample registration number.")

    def approve(self, user):
        self.status = self.Status.APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save(update_fields=["status", "approved_by", "approved_at"])

    def __str__(self) -> str:
        return self.sample_reg_no or f"Booking-{self.pk}"
