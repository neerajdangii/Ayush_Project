from django import forms
from django.db.models import Q
from django.contrib.auth import get_user_model

from .models import Report, ReportRemark, ReportTemplate
from .template_library import build_generic_result_table

DATE_FORMAT_DMY = "%d/%m/%Y"
DATE_INPUT_FORMAT = "%Y-%m-%d"
DATE_PLACEHOLDER = "DD/MM/YYYY"


class ReportApprovalForm(forms.ModelForm):
    incharge_user = forms.ModelChoiceField(
        queryset=get_user_model().objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Person In-charge",
    )
    analysis_start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format=DATE_FORMAT_DMY,
            attrs={
                "type": "text",
                "class": "form-control booking-date-input",
                "placeholder": DATE_PLACEHOLDER,
                "data-picker-kind": "date",
                "data-close-on-pick": "1",
                "autocomplete": "off",
            },
        ),
    )
    analysis_end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format=DATE_FORMAT_DMY,
            attrs={
                "type": "text",
                "class": "form-control booking-date-input",
                "placeholder": DATE_PLACEHOLDER,
                "data-picker-kind": "date",
                "data-close-on-pick": "1",
                "autocomplete": "off",
            },
        ),
    )

    class Meta:
        model = Report
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        UserModel = get_user_model()
        incharge_qs = (
            UserModel.objects.filter(is_active=True, groups__name="Incharge")
            .order_by("first_name", "last_name", "username")
            .distinct()
        )
        self.fields["incharge_user"].queryset = incharge_qs
        self.fields["analysis_start_date"].input_formats = [DATE_INPUT_FORMAT, DATE_FORMAT_DMY]
        self.fields["analysis_end_date"].input_formats = [DATE_INPUT_FORMAT, DATE_FORMAT_DMY]
        if self.instance and self.instance.pk and self.instance.booking_id:
            self.fields["analysis_start_date"].initial = (
                self.instance.booking.analysis_start_date.date() if self.instance.booking.analysis_start_date else None
            )
            self.fields["analysis_end_date"].initial = (
                self.instance.booking.analysis_end_date.date() if self.instance.booking.analysis_end_date else None
            )
            if self.instance.incharge_id:
                self.fields["incharge_user"].initial = self.instance.incharge_id
            else:
                default_incharge = incharge_qs.first()
                if default_incharge:
                    self.fields["incharge_user"].initial = default_incharge.pk


class COAEditForm(forms.ModelForm):
    selected_remarks = forms.ModelMultipleChoiceField(
        queryset=ReportRemark.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "d-none", "id": "id_selected_remarks", "size": 4}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active_remarks = ReportRemark.objects.filter(is_active=True)
        self.fields["selected_remark"].queryset = active_remarks
        self.fields["selected_remarks"].queryset = active_remarks
        if self.instance and self.instance.selected_remark_id:
            self.initial["selected_remarks"] = [self.instance.selected_remark_id]
        current_template_id = self.instance.report_template_id if self.instance else None
        self.fields["report_template"].queryset = ReportTemplate.objects.filter(
            Q(is_active=True) | Q(pk=current_template_id)
        ).select_related("sample_name", "protocol")

        selected_template = self.instance.report_template if self.instance and self.instance.report_template_id else None
        if not selected_template:
            selected_template = self._suggest_template()
        if selected_template:
            self.initial["report_template"] = selected_template.pk

        existing_content = (self.instance.ceo_content or "") if self.instance else ""
        if existing_content:
            self.initial["ceo_content"] = existing_content
        else:
            self.fields["ceo_content"].initial = self._build_default_content(selected_template)

    def _selected_tests(self):
        if not self.instance or not getattr(self.instance, "booking", None):
            return []
        return list(
            self.instance.booking.test_to_be_performed.select_related("report_template").order_by("name")
        )

    def _build_default_content(self, selected_template=None):
        tests = self._selected_tests()
        plain_test_names = []
        template_html_blocks = []
        seen_template_ids = set()

        for test in tests:
            template = getattr(test, "report_template", None)
            if template and template.is_active and template.content.strip():
                if template.pk not in seen_template_ids:
                    template_html_blocks.append(template.content.strip())
                    seen_template_ids.add(template.pk)
            else:
                plain_test_names.append(test.name)

        content_blocks = []
        if plain_test_names:
            content_blocks.append(build_generic_result_table(plain_test_names))

        if selected_template and selected_template.is_active and selected_template.content.strip():
            if selected_template.pk not in seen_template_ids:
                content_blocks.append(selected_template.content.strip())
                seen_template_ids.add(selected_template.pk)

        content_blocks.extend(template_html_blocks)

        if not content_blocks:
            return build_generic_result_table([])

        return "\n<p>&nbsp;</p>\n".join(content_blocks)

    def _suggest_template(self):
        if not self.instance or not getattr(self.instance, "booking", None):
            return None

        booking = self.instance.booking
        test_template = (
            booking.test_to_be_performed.filter(report_template__is_active=True)
            .select_related("report_template")
            .order_by("name")
            .first()
        )
        if test_template and test_template.report_template_id:
            return test_template.report_template

        queryset = ReportTemplate.objects.filter(is_active=True)
        default_template = queryset.filter(is_default=True).first()
        if booking.sample_name_id and booking.protocol_id:
            exact = queryset.filter(sample_name_id=booking.sample_name_id, protocol_id=booking.protocol_id).first()
            if exact:
                return exact
        if booking.sample_name_id:
            by_sample = queryset.filter(sample_name_id=booking.sample_name_id, protocol__isnull=True).first()
            if by_sample:
                return by_sample
        if booking.protocol_id:
            by_protocol = queryset.filter(sample_name__isnull=True, protocol_id=booking.protocol_id).first()
            if by_protocol:
                return by_protocol
        return default_template or queryset.filter(sample_name__isnull=True, protocol__isnull=True).first()

    def clean(self):
        cleaned_data = super().clean()
        selected_remarks = list(cleaned_data.get("selected_remarks") or [])
        remark_text = (cleaned_data.get("remark_text") or "").strip()

        if selected_remarks:
            cleaned_data["selected_remark"] = selected_remarks[0]
        else:
            cleaned_data["selected_remark"] = None

        if selected_remarks and not remark_text:
            cleaned_data["remark_text"] = "\n".join(
                content for content in [remark.content.strip() for remark in selected_remarks] if content
            )

        return cleaned_data

    def clean_ceo_content(self):
        return (self.cleaned_data.get("ceo_content") or "").strip()

    class Meta:
        model = Report
        fields = ["report_template", "ceo_content", "final_outcome", "selected_remarks", "selected_remark", "remark_text"]
        widgets = {
            "report_template": forms.Select(attrs={"class": "form-select", "id": "id_report_template"}),
            "ceo_content": forms.Textarea(
                attrs={
                    "class": "form-control tinymce-editor",
                    "id": "editor",
                    "rows": 16,
                    "data-editor": "tinymce",
                }
            ),
            "final_outcome": forms.Select(attrs={"class": "form-select"}),
            "selected_remark": forms.HiddenInput(),
            "remark_text": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }
        labels = {
            "report_template": "Report Template",
            "ceo_content": "CEO Content",
            "final_outcome": "Final Outcome",
            "selected_remarks": "Remark Master",
            "remark_text": "Remarks",
        }


class ReportTemplateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sample_name"].queryset = self.fields["sample_name"].queryset.filter(is_active=True)
        self.fields["protocol"].queryset = self.fields["protocol"].queryset.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("is_default"):
            cleaned_data["is_active"] = True
        return cleaned_data

    class Meta:
        model = ReportTemplate
        fields = ["name", "sample_name", "protocol", "description", "content", "is_active", "is_default"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "sample_name": forms.Select(attrs={"class": "form-select"}),
            "protocol": forms.Select(attrs={"class": "form-select"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control tinymce-editor",
                    "rows": 18,
                    "data-editor": "tinymce",
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_default": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_content(self):
        return (self.cleaned_data.get("content") or "").strip()
