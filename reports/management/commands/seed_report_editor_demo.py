from django.core.management.base import BaseCommand

from reports.models import ReportTemplate
from reports.template_library import VITAMIN_ANALYSIS_REPORT_HTML, VITAMIN_ANALYSIS_REPORT_NAME


class Command(BaseCommand):
    help = "Create a sample report editor template for TinyMCE-based lab reports."

    def handle(self, *args, **options):
        template, created = ReportTemplate.objects.update_or_create(
            name=VITAMIN_ANALYSIS_REPORT_NAME,
            defaults={
                "description": "Real extracted vitamin analysis report template from the legacy editor.",
                "content": VITAMIN_ANALYSIS_REPORT_HTML,
                "is_active": True,
            },
        )

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} template: {template.name}"))
