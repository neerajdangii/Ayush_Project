from __future__ import annotations

from django.db import migrations


def assign_numeric_codes(apps, schema_editor):
    Booking = apps.get_model("bookings", "Booking")
    next_value = 1000
    for booking in Booking.objects.order_by("created_at").only("pk", "tracking_code"):
        booking.tracking_code = str(next_value)
        booking.save(update_fields=["tracking_code"])
        next_value += 1


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0005_booking_tracking_code"),
    ]

    operations = [
        migrations.RunPython(assign_numeric_codes, migrations.RunPython.noop),
    ]
