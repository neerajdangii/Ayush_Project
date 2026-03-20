from django import forms

from .models import Report, ReportRemark

DATE_FORMAT_DMY = "%d/%m/%Y"
DATETIME_FORMAT_DMY = "%d/%m/%Y %I:%M %p"
DATE_PLACEHOLDER = "DD/MM/YYYY HH:MM AM"
DEFAULT_COA_RESULT_TEMPLATE = """
<p><em>{{non_nabl_section_started}}</em></p>
<table style="width:100%; border-collapse:collapse;" border="1">
  <tbody>
    <tr>
      <th style="width:8%; padding:6px; text-align:center;">S.No.</th>
      <th style="width:42%; padding:6px; text-align:left;">Test Parameters</th>
      <th style="width:25%; padding:6px; text-align:left;">Results/Observation</th>
      <th style="width:25%; padding:6px; text-align:left;">Specification/Limits</th>
    </tr>
    <tr>
      <td style="padding:6px; text-align:center;">1</td>
      <td style="padding:6px;">&nbsp;</td>
      <td style="padding:6px;">&nbsp;</td>
      <td style="padding:6px;">&nbsp;</td>
    </tr>
    <tr>
      <td style="padding:6px; text-align:center;">2</td>
      <td style="padding:6px;">&nbsp;</td>
      <td style="padding:6px;">&nbsp;</td>
      <td style="padding:6px;">&nbsp;</td>
    </tr>
    <tr>
      <th style="padding:6px; text-align:center;">COMPOSITION</th>
      <th style="padding:6px; text-align:center;">RESULTS</th>
      <th style="padding:6px; text-align:center;">LABEL CLAIM</th>
      <th style="padding:6px; text-align:center;">% LABEL CLAIM</th>
      <th style="padding:6px; text-align:center;">LIMITS</th>
      <th style="padding:6px; text-align:center;">METHOD</th>
    </tr>
    <tr>
      <td style="padding:6px;">&nbsp;</td>
      <td style="padding:6px;">&nbsp;</td>
      <td style="padding:6px;">&nbsp;</td>
      <td style="padding:6px;">&nbsp;</td>
      <td style="padding:6px;">&nbsp;</td>
      <td style="padding:6px;">&nbsp;</td>
    </tr>
  </tbody>
</table>
<p>&nbsp;</p>
"""


class ReportApprovalForm(forms.ModelForm):
    analysis_start_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            format=DATETIME_FORMAT_DMY,
            attrs={"type": "text", "class": "form-control", "placeholder": DATE_PLACEHOLDER},
        ),
    )
    analysis_end_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            format=DATETIME_FORMAT_DMY,
            attrs={"type": "text", "class": "form-control", "placeholder": DATE_PLACEHOLDER},
        ),
    )

    class Meta:
        model = Report
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["analysis_start_date"].input_formats = [DATETIME_FORMAT_DMY]
        self.fields["analysis_end_date"].input_formats = [DATETIME_FORMAT_DMY]
        if self.instance and self.instance.pk and self.instance.booking_id:
            self.fields["analysis_start_date"].initial = self.instance.booking.analysis_start_date
            self.fields["analysis_end_date"].initial = self.instance.booking.analysis_end_date


class COAEditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["selected_remark"].queryset = ReportRemark.objects.filter(is_active=True)
        if self.instance and not (self.instance.ceo_content or "").strip():
            self.fields["ceo_content"].initial = DEFAULT_COA_RESULT_TEMPLATE

    def clean(self):
        cleaned_data = super().clean()
        selected_remark = cleaned_data.get("selected_remark")
        remark_text = (cleaned_data.get("remark_text") or "").strip()

        if selected_remark and not remark_text:
            cleaned_data["remark_text"] = selected_remark.content

        return cleaned_data

    class Meta:
        model = Report
        fields = ["ceo_content", "final_outcome", "selected_remark", "remark_text"]
        widgets = {
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
            "ceo_content": "CEO Content",
            "final_outcome": "Final Outcome",
            "selected_remark": "Remark Master",
            "remark_text": "Remarks",
        }
