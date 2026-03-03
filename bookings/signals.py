from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def ensure_default_roles(sender, **kwargs):
    # Ensure core role groups exist across environments.
    for role in ("Admin", "Manager", "Incharge", "Analyst"):
        Group.objects.get_or_create(name=role)

    role_permissions = {
        "Analyst": {
            "bookings.add_booking",
            "bookings.view_booking",
            "bookings.view_customermaster",
            "bookings.view_submittermaster",
            "bookings.view_manufacturermaster",
            "bookings.view_samplenamemaster",
            "bookings.view_testmaster",
            "bookings.view_protocolmaster",
            "bookings.view_uommaster",
            "reports.view_report",
        },
        "Manager": {
            "bookings.view_booking",
            "bookings.change_booking",
            "reports.view_report",
            "reports.change_report",
        },
        "Incharge": {
            "bookings.view_booking",
            "reports.view_report",
            "reports.change_report",
        },
        "Admin": {
            "bookings.add_booking",
            "bookings.change_booking",
            "bookings.delete_booking",
            "bookings.view_booking",
            "bookings.add_customermaster",
            "bookings.change_customermaster",
            "bookings.delete_customermaster",
            "bookings.view_customermaster",
            "bookings.add_submittermaster",
            "bookings.change_submittermaster",
            "bookings.delete_submittermaster",
            "bookings.view_submittermaster",
            "bookings.add_manufacturermaster",
            "bookings.change_manufacturermaster",
            "bookings.delete_manufacturermaster",
            "bookings.view_manufacturermaster",
            "bookings.add_samplenamemaster",
            "bookings.change_samplenamemaster",
            "bookings.delete_samplenamemaster",
            "bookings.view_samplenamemaster",
            "bookings.add_testmaster",
            "bookings.change_testmaster",
            "bookings.delete_testmaster",
            "bookings.view_testmaster",
            "bookings.add_protocolmaster",
            "bookings.change_protocolmaster",
            "bookings.delete_protocolmaster",
            "bookings.view_protocolmaster",
            "bookings.add_uommaster",
            "bookings.change_uommaster",
            "bookings.delete_uommaster",
            "bookings.view_uommaster",
            "reports.add_report",
            "reports.change_report",
            "reports.delete_report",
            "reports.view_report",
        },
    }

    permission_map = {
        f"{perm.content_type.app_label}.{perm.codename}": perm
        for perm in Permission.objects.select_related("content_type")
    }
    for role, perms in role_permissions.items():
        group = Group.objects.get(name=role)
        group.permissions.set([permission_map[key] for key in perms if key in permission_map])
