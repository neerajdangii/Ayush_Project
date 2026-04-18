from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission


ROLE_PERMISSIONS = {
    "Staff": {
        "bookings.add_booking",
        "bookings.change_booking",
        "bookings.view_booking",
    },
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
    "Checked By": {
        "bookings.view_booking",
        "bookings.change_booking",
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


def sync_role_permissions(*, sync_staff_membership: bool = True) -> dict[str, int]:
    permission_map = {
        f"{perm.content_type.app_label}.{perm.codename}": perm
        for perm in Permission.objects.select_related("content_type")
    }

    synced_groups = 0
    for role, permission_keys in ROLE_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=role)
        group.permissions.set([permission_map[key] for key in permission_keys if key in permission_map])
        synced_groups += 1

    staff_members_synced = 0
    if sync_staff_membership:
        staff_group = Group.objects.get(name="Staff")
        UserModel = get_user_model()
        for user in UserModel.objects.filter(is_staff=True):
            staff_group.user_set.add(user)
            staff_members_synced += 1

    return {
        "groups": synced_groups,
        "staff_members": staff_members_synced,
    }
