from django import forms

from .models import Report

DATE_FORMAT_DMY = "%d/%m/%Y"
DATE_PLACEHOLDER = "DD/MM/YYYY"


class ReportApprovalForm(forms.ModelForm):
    analysis_start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format=DATE_FORMAT_DMY,
            attrs={"type": "text", "class": "form-control", "placeholder": DATE_PLACEHOLDER},
        ),
    )
    report_end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format=DATE_FORMAT_DMY,
            attrs={"type": "text", "class": "form-control", "placeholder": DATE_PLACEHOLDER},
        ),
    )

    class Meta:
        model = Report
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["analysis_start_date"].input_formats = [DATE_FORMAT_DMY]
        self.fields["report_end_date"].input_formats = [DATE_FORMAT_DMY]
        if self.instance and self.instance.pk and self.instance.booking_id:
            self.fields["analysis_start_date"].initial = self.instance.booking.analysis_start_date
            self.fields["report_end_date"].initial = self.instance.booking.analysis_end_date


class COAEditForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["ceo_content"]
        widgets = {
            "ceo_content": forms.Textarea(attrs={"class": "form-control", "rows": 16}),
        }
