from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .roles import sync_role_permissions
from .models import Booking


@receiver(post_migrate)
def ensure_default_roles(sender, **kwargs):
    sync_role_permissions(sync_staff_membership=True)


@receiver(post_save, sender=Booking)
def sync_booking_dates_to_report(sender, instance, created, **kwargs):
    """
    When a booking is saved, sync the analysis dates to the related report.
    This ensures that changes to booking dates are immediately reflected in reports.
    """
    if hasattr(instance, 'report'):
        try:
            report = instance.report
            # Update the report's analysis_end_date with the booking's analysis_end_date
            if instance.analysis_end_date and report.analysis_end_date != instance.analysis_end_date:
                report.analysis_end_date = instance.analysis_end_date
                report.save(update_fields=['analysis_end_date'])
        except Exception:
            # If report doesn't exist yet, that's fine - it will be created later
            pass
