from django import forms

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
DATE_PLACEHOLDER = "DD/MM/YYYY"


class BookingForm(forms.ModelForm):
    DATE_INPUT_FIELDS = [
        "booking_date",
        "letter_date",
        "sampling_upto",
        "sample_receipt_date",
        "manufacture_date",
        "expiry_retest_date",
            "analysis_start_date",
            "analysis_end_date",
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
            "collected_by_name",
            "sampling_procedure",
            "analysis_start_date",
            "analysis_end_date",
            "remarks",
        ]
        widgets = {
            "booking_date": forms.DateInput(
                format=DATE_FORMAT_DMY,
                attrs={"type": "text", "class": "form-control", "placeholder": DATE_PLACEHOLDER},
            ),
            "letter_date": forms.DateInput(
                format=DATE_FORMAT_DMY,
                attrs={"type": "text", "class": "form-control", "placeholder": DATE_PLACEHOLDER},
            ),
            "sampling_upto": forms.DateInput(
                format=DATE_FORMAT_DMY,
                attrs={"type": "text", "class": "form-control", "placeholder": DATE_PLACEHOLDER},
            ),
            "sample_receipt_date": forms.DateInput(
                format=DATE_FORMAT_DMY,
                attrs={"type": "text", "class": "form-control", "placeholder": DATE_PLACEHOLDER},
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
                format=DATE_FORMAT_DMY,
                attrs={"type": "text", "class": "form-control", "placeholder": DATE_PLACEHOLDER},
            ),
            "expiry_retest_date": forms.DateInput(
                format=DATE_FORMAT_DMY,
                attrs={"type": "text", "class": "form-control", "placeholder": DATE_PLACEHOLDER},
            ),
            "collected_by_name": forms.TextInput(attrs={"class": "form-control"}),
            "sampling_procedure": forms.TextInput(attrs={"class": "form-control"}),
            "analysis_start_date": forms.DateInput(
                format=DATE_FORMAT_DMY,
                attrs={"type": "text", "class": "form-control", "placeholder": DATE_PLACEHOLDER},
            ),
            "analysis_end_date": forms.DateInput(
                format=DATE_FORMAT_DMY,
                attrs={"type": "text", "class": "form-control", "placeholder": DATE_PLACEHOLDER},
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
        for field_name in self.DATE_INPUT_FIELDS:
            self.fields[field_name].input_formats = [DATE_FORMAT_DMY]

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
