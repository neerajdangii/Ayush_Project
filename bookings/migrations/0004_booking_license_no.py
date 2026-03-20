from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0003_booking_analysis_end_date_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="license_no",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
