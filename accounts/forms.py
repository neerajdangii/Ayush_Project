from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import Group, User

from .models import UserProfile


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))

    error_messages = {
        "invalid_login": "Invalid username or password.",
        "inactive": "This user account is inactive.",
    }


class AdminUserCreateForm(UserCreationForm):
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))
    is_staff = forms.BooleanField(required=False)
    is_checked_by = forms.BooleanField(required=False, label="Checked By")
    is_person_incharge = forms.BooleanField(required=False, label="Person In-charge")
    signature_file = forms.FileField(required=False)
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.filter(name__in=["Admin", "Manager", "Analyst"]).order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
            "is_staff",
            "is_checked_by",
            "is_person_incharge",
            "signature_file",
            "groups",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["class"] = "form-control"
        self.fields["password1"].widget.attrs["class"] = "form-control"
        self.fields["password2"].widget.attrs["class"] = "form-control"
        self.fields["is_staff"].widget.attrs["class"] = "form-check-input"
        self.fields["is_checked_by"].widget.attrs["class"] = "form-check-input"
        self.fields["is_person_incharge"].widget.attrs["class"] = "form-check-input"
        self.fields["signature_file"].widget.attrs["class"] = "form-control"

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "")
        user.first_name = (self.cleaned_data.get("first_name") or "").strip()
        user.last_name = (self.cleaned_data.get("last_name") or "").strip()
        checked_by = bool(self.cleaned_data.get("is_checked_by"))
        person_incharge = bool(self.cleaned_data.get("is_person_incharge"))
        user.is_staff = bool(self.cleaned_data.get("is_staff", False)) or checked_by or person_incharge
        if commit:
            user.save()
            user.groups.set(self.cleaned_data.get("groups"))
            if user.is_staff:
                staff_group, _ = Group.objects.get_or_create(name="Staff")
                staff_group.user_set.add(user)
            if checked_by:
                group, _ = Group.objects.get_or_create(name="Checked By")
                group.user_set.add(user)
            if person_incharge:
                group, _ = Group.objects.get_or_create(name="Incharge")
                group.user_set.add(user)

            signature_file = self.cleaned_data.get("signature_file")
            if signature_file:
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.signature_file = signature_file
                profile.save(update_fields=["signature_file"])
        return user


class AdminUserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))
    is_staff = forms.BooleanField(required=False)
    is_active = forms.BooleanField(required=False)
    is_checked_by = forms.BooleanField(required=False, label="Checked By")
    is_person_incharge = forms.BooleanField(required=False, label="Person In-charge")
    signature_file = forms.FileField(required=False)
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.filter(name__in=["Admin", "Manager", "Analyst"]).order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_staff",
            "is_checked_by",
            "is_person_incharge",
            "signature_file",
            "groups",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs["class"] = "form-control"
        self.fields["first_name"].widget.attrs["class"] = "form-control"
        self.fields["last_name"].widget.attrs["class"] = "form-control"
        self.fields["is_staff"].widget.attrs["class"] = "form-check-input"
        self.fields["is_active"].widget.attrs["class"] = "form-check-input"
        self.fields["is_checked_by"].widget.attrs["class"] = "form-check-input"
        self.fields["is_person_incharge"].widget.attrs["class"] = "form-check-input"
        self.fields["signature_file"].widget.attrs["class"] = "form-control"

        if self.instance and getattr(self.instance, "pk", None):
            self.fields["is_active"].initial = bool(self.instance.is_active)
            self.fields["is_staff"].initial = bool(self.instance.is_staff)
            self.fields["is_checked_by"].initial = self.instance.groups.filter(name="Checked By").exists()
            self.fields["is_person_incharge"].initial = self.instance.groups.filter(name="Incharge").exists()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "")
        user.first_name = (self.cleaned_data.get("first_name") or "").strip()
        user.last_name = (self.cleaned_data.get("last_name") or "").strip()

        checked_by = bool(self.cleaned_data.get("is_checked_by"))
        person_incharge = bool(self.cleaned_data.get("is_person_incharge"))
        user.is_active = bool(self.cleaned_data.get("is_active", True))
        user.is_staff = bool(self.cleaned_data.get("is_staff", False)) or checked_by or person_incharge

        if commit:
            user.save()

            managed_group_names = {"Admin", "Manager", "Analyst", "Checked By", "Incharge", "Staff"}
            existing_groups = list(user.groups.all())
            preserved_groups = [g for g in existing_groups if g.name not in managed_group_names]

            selected_groups = list(self.cleaned_data.get("groups") or [])
            desired_groups = preserved_groups + selected_groups

            staff_group, _ = Group.objects.get_or_create(name="Staff")
            checked_by_group, _ = Group.objects.get_or_create(name="Checked By")
            incharge_group, _ = Group.objects.get_or_create(name="Incharge")

            if user.is_staff and staff_group not in desired_groups:
                desired_groups.append(staff_group)
            if checked_by and checked_by_group not in desired_groups:
                desired_groups.append(checked_by_group)
            if not checked_by and checked_by_group in desired_groups:
                desired_groups = [g for g in desired_groups if g.pk != checked_by_group.pk]
            if person_incharge and incharge_group not in desired_groups:
                desired_groups.append(incharge_group)
            if not person_incharge and incharge_group in desired_groups:
                desired_groups = [g for g in desired_groups if g.pk != incharge_group.pk]

            if not user.is_staff and staff_group in desired_groups:
                desired_groups = [g for g in desired_groups if g.pk != staff_group.pk]

            user.groups.set(desired_groups)

            signature_clear = self.data.get("signature_file-clear") == "on"
            signature_file = self.cleaned_data.get("signature_file")
            if signature_clear or signature_file:
                profile, _ = UserProfile.objects.get_or_create(user=user)
                if signature_clear:
                    if profile.signature_file:
                        profile.signature_file.delete(save=False)
                    profile.signature_file = None
                else:
                    profile.signature_file = signature_file
                profile.save()

        return user
