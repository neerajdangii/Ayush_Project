from __future__ import annotations

from django.db import migrations, models
import secrets


def populate_tracking_codes(apps, schema_editor):
    Booking = apps.get_model('bookings', 'Booking')
    existing = set(Booking.objects.exclude(tracking_code="").values_list('tracking_code', flat=True))

    def generate_code():
        for _ in range(10):
            code = f"ARL-{secrets.token_hex(4).upper()}"
            if code not in existing and not Booking.objects.filter(tracking_code=code).exists():
                existing.add(code)
                return code
        raise RuntimeError('Unable to generate unique booking ID')

    for booking in Booking.objects.all():
        if not booking.tracking_code:
            booking.tracking_code = generate_code()
            booking.save(update_fields=['tracking_code'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0004_booking_license_no'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='tracking_code',
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=16,
                default="",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(populate_tracking_codes, noop),
        migrations.AlterField(
            model_name='booking',
            name='tracking_code',
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=16,
                unique=True,
            ),
        ),
    ]
