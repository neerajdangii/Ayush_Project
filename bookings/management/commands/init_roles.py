from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User

class Command(BaseCommand):
    help = "Create default role groups and assign basic bookings permissions. Optionally add a user to Analyst group."

    def add_arguments(self, parser):
        parser.add_argument("--username", help="Username to add to Analyst group", required=False)

    def handle(self, *args, **options):
        roles = ["Admin", "Manager", "Incharge", "Analyst"]
        for role in roles:
            g, created = Group.objects.get_or_create(name=role)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created group: {role}"))
            else:
                self.stdout.write(f"Group exists: {role}")

        # Assign bookings permissions
        bookings_perms = Permission.objects.filter(content_type__app_label="bookings")
        admin_group = Group.objects.get(name="Admin")
        admin_group.permissions.set(bookings_perms)
        self.stdout.write(self.style.SUCCESS("Assigned all bookings permissions to Admin group."))

        # Give Manager change permission
        manager_group = Group.objects.get(name="Manager")
        change_perms = bookings_perms.filter(codename__startswith="change_")
        manager_group.permissions.set(change_perms)
        self.stdout.write(self.style.SUCCESS("Assigned change permissions to Manager group."))

        # Give Analyst only add permissions
        analyst_group = Group.objects.get(name="Analyst")
        add_perms = bookings_perms.filter(codename__startswith="add_")
        analyst_group.permissions.set(add_perms)
        self.stdout.write(self.style.SUCCESS("Assigned add permissions to Analyst group."))

        username = options.get("username")
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User '{username}' does not exist."))
                return
            analyst_group.user_set.add(user)
            self.stdout.write(self.style.SUCCESS(f"Added user '{username}' to Analyst group."))

        self.stdout.write(self.style.SUCCESS("Role initialization complete."))
