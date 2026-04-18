from django.core.management.base import BaseCommand

from bookings.roles import sync_role_permissions

class Command(BaseCommand):
    help = "Sync default role groups, permissions, and Staff membership."

    def handle(self, *args, **options):
        result = sync_role_permissions(sync_staff_membership=True)
        self.stdout.write(self.style.SUCCESS(f"Synced {result['groups']} role groups."))
        self.stdout.write(self.style.SUCCESS(f"Backfilled {result['staff_members']} staff memberships."))
