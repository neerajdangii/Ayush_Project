from django import forms

from reports.models import ReportRemark

from .models import (
    Booking,
    CustomerMaster,
    ManufacturerMaster,
    ProtocolMaster,
    SampleNameMaster,
    SubmitterMaster,
    TestMaster,
    UOMMaster,
)

DATE_FORMAT_DMY = "%d/%m/%Y"
DATETIME_FORMAT_DMY = "%d/%m/%Y %I:%M %p"
DATE_INPUT_FORMAT = "%Y-%m-%d"
DATETIME_LOCAL_INPUT_FORMAT = "%Y-%m-%dT%H:%M"
DATE_PLACEHOLDER = "DD/MM/YYYY"
DATETIME_PLACEHOLDER = "DD/MM/YYYY HH:MM AM"


class BookingForm(forms.ModelForm):
    DATETIME_INPUT_FIELDS = [
        "booking_date",
        "letter_date",
        "sampling_upto",
        "sample_receipt_date",
        "analysis_start_date",
        "analysis_end_date",
    ]
    DATE_INPUT_FIELDS = [
        "manufacture_date",
        "expiry_retest_date",
    ]

    class Meta:
        model = Booking
        fields = [
            "booking_date",
            "letter_date",
            "sampling_upto",
            "sample_receipt_date",
            "customer",
            "submitter",
            "manufacturer",
            "sample_name",
            "sample_type",
            "test_to_be_performed",
            "protocol",
            "uom",
            "booking_type",
            "sample_qty",
            "sample_location",
            "packaging_mode",
            "sample_condition",
            "batch_no",
            "batch_size",
            "manufacture_date",
            "expiry_retest_date",
            "license_no",
            "collected_by_name",
            "sampling_procedure",
            "analysis_start_date",
            "analysis_end_date",
            "remarks",
        ]
        widgets = {
            "booking_date": forms.DateTimeInput(
                format=DATETIME_LOCAL_INPUT_FORMAT,
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                    "step": "60",
                },
            ),
            "letter_date": forms.DateTimeInput(
                format=DATETIME_LOCAL_INPUT_FORMAT,
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                    "step": "60",
                },
            ),
            "sampling_upto": forms.DateTimeInput(
                format=DATETIME_LOCAL_INPUT_FORMAT,
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                    "step": "60",
                },
            ),
            "sample_receipt_date": forms.DateTimeInput(
                format=DATETIME_LOCAL_INPUT_FORMAT,
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                    "step": "60",
                },
            ),
            "customer": forms.Select(attrs={"class": "form-select"}),
            "submitter": forms.Select(attrs={"class": "form-select"}),
            "manufacturer": forms.Select(attrs={"class": "form-select"}),
            "sample_name": forms.Select(attrs={"class": "form-select"}),
            "sample_type": forms.Select(attrs={"class": "form-select"}),
            "test_to_be_performed": forms.SelectMultiple(attrs={"class": "form-select", "size": 6}),
            "protocol": forms.Select(attrs={"class": "form-select"}),
            "uom": forms.Select(attrs={"class": "form-select"}),
            "booking_type": forms.Select(attrs={"class": "form-select"}),
            "sample_qty": forms.TextInput(attrs={"class": "form-control"}),
            "sample_location": forms.TextInput(attrs={"class": "form-control"}),
            "packaging_mode": forms.TextInput(attrs={"class": "form-control"}),
            "sample_condition": forms.TextInput(attrs={"class": "form-control"}),
            "batch_no": forms.TextInput(attrs={"class": "form-control"}),
            "batch_size": forms.TextInput(attrs={"class": "form-control"}),
            "manufacture_date": forms.DateInput(
                format=DATE_INPUT_FORMAT,
                attrs={
                    "type": "date",
                    "class": "form-control",
                },
            ),
            "expiry_retest_date": forms.DateInput(
                format=DATE_INPUT_FORMAT,
                attrs={
                    "type": "date",
                    "class": "form-control",
                },
            ),
            "license_no": forms.TextInput(attrs={"class": "form-control"}),
            "collected_by_name": forms.TextInput(attrs={"class": "form-control"}),
            "sampling_procedure": forms.TextInput(attrs={"class": "form-control"}),
            "analysis_start_date": forms.DateTimeInput(
                format=DATETIME_LOCAL_INPUT_FORMAT,
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                    "step": "60",
                },
            ),
            "analysis_end_date": forms.DateTimeInput(
                format=DATETIME_LOCAL_INPUT_FORMAT,
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                    "step": "60",
                },
            ),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_fields = [
            "booking_date",
            "customer",
            "submitter",
            "manufacturer",
            "sample_name",
            "sample_type",
            "test_to_be_performed",
            "protocol",
            "uom",
            "booking_type",
        ]
        for field_name in required_fields:
            self.fields[field_name].required = True
        for field_name in self.DATETIME_INPUT_FIELDS:
            self.fields[field_name].input_formats = [DATETIME_LOCAL_INPUT_FORMAT, DATETIME_FORMAT_DMY]
        for field_name in self.DATE_INPUT_FIELDS:
            self.fields[field_name].input_formats = [DATE_INPUT_FORMAT, DATE_FORMAT_DMY, DATETIME_FORMAT_DMY]

        self.fields["customer"].queryset = CustomerMaster.objects.filter(is_active=True)
        self.fields["submitter"].queryset = SubmitterMaster.objects.filter(is_active=True)
        self.fields["manufacturer"].queryset = ManufacturerMaster.objects.filter(is_active=True)
        self.fields["sample_name"].queryset = SampleNameMaster.objects.filter(is_active=True)
        self.fields["test_to_be_performed"].queryset = TestMaster.objects.filter(is_active=True)
        self.fields["protocol"].queryset = ProtocolMaster.objects.filter(is_active=True)
        self.fields["uom"].queryset = UOMMaster.objects.filter(is_active=True)


class MasterForm(forms.ModelForm):
    class Meta:
        fields = ["name", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class CustomerMasterForm(MasterForm):
    class Meta(MasterForm.Meta):
        model = CustomerMaster


class SubmitterMasterForm(MasterForm):
    class Meta(MasterForm.Meta):
        model = SubmitterMaster


class ManufacturerMasterForm(MasterForm):
    class Meta(MasterForm.Meta):
        model = ManufacturerMaster


class SampleNameMasterForm(MasterForm):
    class Meta(MasterForm.Meta):
        model = SampleNameMaster


class TestMasterForm(MasterForm):
    class Meta(MasterForm.Meta):
        model = TestMaster


class ProtocolMasterForm(MasterForm):
    class Meta(MasterForm.Meta):
        model = ProtocolMaster


class UOMMasterForm(MasterForm):
    class Meta(MasterForm.Meta):
        model = UOMMaster


class ReportRemarkMasterForm(forms.ModelForm):
    class Meta:
        model = ReportRemark
        fields = ["title", "content", "sort_order", "is_active"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
