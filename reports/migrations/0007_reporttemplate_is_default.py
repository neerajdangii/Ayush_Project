from django.db import migrations, models


def set_first_template_default(apps, schema_editor):
    ReportTemplate = apps.get_model("reports", "ReportTemplate")
    default_template = ReportTemplate.objects.order_by("created_at", "pk").first()
    if default_template and not ReportTemplate.objects.filter(is_default=True).exists():
        default_template.is_default = True
        default_template.save(update_fields=["is_default"])


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0006_reporttemplate_report_report_template"),
    ]

    operations = [
        migrations.AddField(
            model_name="reporttemplate",
            name="is_default",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(set_first_template_default, migrations.RunPython.noop),
    ]
