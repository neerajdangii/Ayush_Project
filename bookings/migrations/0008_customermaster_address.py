from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0007_alter_booking_analysis_end_date_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="customermaster",
            name="address",
            field=models.TextField(blank=True),
        ),
    ]
