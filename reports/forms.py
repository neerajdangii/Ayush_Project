from django import forms
from django.db.models import Q

from .models import Report, ReportRemark, ReportTemplate
from .render_utils import normalize_report_table_html
from .template_library import VITAMIN_ANALYSIS_REPORT_HTML

DATE_FORMAT_DMY = "%d/%m/%Y"
DATE_INPUT_FORMAT = "%Y-%m-%d"
DATE_PLACEHOLDER = "YYYY-MM-DD"
DEFAULT_COA_RESULT_TEMPLATE = VITAMIN_ANALYSIS_REPORT_HTML


class ReportApprovalForm(forms.ModelForm):
    analysis_start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format=DATE_INPUT_FORMAT,
            attrs={"type": "date", "class": "form-control", "placeholder": DATE_PLACEHOLDER},
        ),
    )
    analysis_end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format=DATE_INPUT_FORMAT,
            attrs={"type": "date", "class": "form-control", "placeholder": DATE_PLACEHOLDER},
        ),
    )

    class Meta:
        model = Report
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["analysis_start_date"].input_formats = [DATE_INPUT_FORMAT]
        self.fields["analysis_end_date"].input_formats = [DATE_INPUT_FORMAT]
        if self.instance and self.instance.pk and self.instance.booking_id:
            self.fields["analysis_start_date"].initial = (
                self.instance.booking.analysis_start_date.date() if self.instance.booking.analysis_start_date else None
            )
            self.fields["analysis_end_date"].initial = (
                self.instance.booking.analysis_end_date.date() if self.instance.booking.analysis_end_date else None
            )


class COAEditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["selected_remark"].queryset = ReportRemark.objects.filter(is_active=True)
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
        normalized_content = normalize_report_table_html(existing_content)
        if normalized_content:
            self.initial["ceo_content"] = normalized_content
        elif selected_template:
            self.initial["ceo_content"] = normalize_report_table_html(selected_template.content)
        else:
            self.fields["ceo_content"].initial = DEFAULT_COA_RESULT_TEMPLATE

    def _suggest_template(self):
        if not self.instance or not getattr(self.instance, "booking", None):
            return None

        booking = self.instance.booking
        queryset = ReportTemplate.objects.filter(is_active=True)
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
        return queryset.filter(sample_name__isnull=True, protocol__isnull=True).first()

    def clean(self):
        cleaned_data = super().clean()
        selected_remark = cleaned_data.get("selected_remark")
        remark_text = (cleaned_data.get("remark_text") or "").strip()

        if selected_remark and not remark_text:
            cleaned_data["remark_text"] = selected_remark.content

        return cleaned_data

    def clean_ceo_content(self):
        return normalize_report_table_html(self.cleaned_data.get("ceo_content") or "")

    class Meta:
        model = Report
        fields = ["report_template", "ceo_content", "final_outcome", "selected_remark", "remark_text"]
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
            "selected_remark": forms.Select(attrs={"class": "form-select", "id": "id_selected_remark"}),
            "remark_text": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }
        labels = {
            "report_template": "Report Template",
            "ceo_content": "CEO Content",
            "final_outcome": "Final Outcome",
            "selected_remark": "Remark Master",
            "remark_text": "Remarks",
        }


class ReportTemplateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sample_name"].queryset = self.fields["sample_name"].queryset.filter(is_active=True)
        self.fields["protocol"].queryset = self.fields["protocol"].queryset.filter(is_active=True)

    class Meta:
        model = ReportTemplate
        fields = ["name", "sample_name", "protocol", "description", "content", "is_active"]
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
        }

    def clean_content(self):
        return normalize_report_table_html(self.cleaned_data.get("content") or "")
