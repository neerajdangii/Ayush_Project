from __future__ import annotations

from django.db import migrations


def create_staff_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    User = apps.get_model("auth", "User")

    staff_group, _ = Group.objects.get_or_create(name="Staff")

    perms = Permission.objects.filter(content_type__app_label__in=["bookings", "reports"])
    staff_group.permissions.set(perms)

    for user in User.objects.filter(is_staff=True):
        staff_group.user_set.add(user)


def remove_staff_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="Staff").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_staff_group, reverse_code=remove_staff_group),
    ]

