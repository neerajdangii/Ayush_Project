from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect


def has_role(user, role_name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=role_name).exists()


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    required_roles = ()

    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        return any(has_role(user, role) for role in self.required_roles)

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to access this page.")
        return redirect("dashboard")
