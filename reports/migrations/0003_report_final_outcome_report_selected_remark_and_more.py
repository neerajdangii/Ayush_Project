from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0002_alter_report_options_remove_report_generated_by_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReportRemark",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("content", models.TextField()),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["sort_order", "title"],
            },
        ),
        migrations.AddField(
            model_name="report",
            name="final_outcome",
            field=models.CharField(
                choices=[("draft", "Draft"), ("pass", "Pass")],
                default="draft",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="report",
            name="remark_text",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="report",
            name="selected_remark",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reports",
                to="reports.reportremark",
            ),
        ),
    ]
