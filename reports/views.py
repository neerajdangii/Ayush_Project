from __future__ import annotations

from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView, RedirectView, TemplateView, UpdateView

from bookings.models import Booking
from bookings.permissions import RoleRequiredMixin, has_role

from .forms import COAEditForm, ReportApprovalForm
from .models import Report


def _format_report_date(value, include_time=False, month_year_only=False):
    if not value:
        return "-"

    if isinstance(value, datetime):
        current = timezone.localtime(value) if timezone.is_aware(value) else value
        if month_year_only:
            return current.strftime("%m/%Y")
        return current.strftime("%d/%m/%Y %I:%M %p") if include_time else current.strftime("%d/%m/%Y")

    if isinstance(value, date):
        if month_year_only:
            return value.strftime("%m/%Y")
        return value.strftime("%d/%m/%Y")

    return value


def _build_report_date_context(report):
    booking = report.booking
    return {
        "report_letter_date": _format_report_date(booking.letter_date, include_time=True),
        "report_received_date": _format_report_date(booking.sample_receipt_date, include_time=True),
        "report_analysis_start_date": _format_report_date(booking.analysis_start_date, include_time=True),
        "report_analysis_end_date": _format_report_date(report.analysis_end_date, include_time=True),
        "report_manufacture_date": _format_report_date(booking.manufacture_date, month_year_only=True),
        "report_expiry_date": _format_report_date(booking.expiry_retest_date, month_year_only=True),
    }


class ReportListView(PermissionRequiredMixin, RoleRequiredMixin, ListView):
    permission_required = "reports.view_report"
    required_roles = ("Manager", "Incharge", "Analyst")
    model = Report
    template_name = "reports/report_list.html"
    context_object_name = "reports"
    paginate_by = 10

    def get_queryset(self):
        existing_booking_ids = Report.objects.values_list("booking_id", flat=True)
        missing_approved_bookings = Booking.objects.filter(status=Booking.Status.APPROVED).exclude(
            pk__in=existing_booking_ids
        )
        if missing_approved_bookings.exists():
            Report.objects.bulk_create(
                [Report(booking=booking, created_by=booking.approved_by or booking.created_by) for booking in missing_approved_bookings]
            )

        qs = Report.objects.select_related(
            "booking",
            "booking__customer",
            "booking__sample_name",
            "manager",
            "incharge",
        ).order_by("-created_at")
        search = self.request.GET.get("q", "").strip()
        search_by = self.request.GET.get("search_by", "sample_reg").strip()
        if search:
            if search_by == "booking_id":
                qs = qs.filter(booking__tracking_code__icontains=search)
            elif search_by == "batch_no":
                qs = qs.filter(booking__batch_no__icontains=search)
            elif search_by == "customer":
                qs = qs.filter(booking__customer__name__icontains=search)
            elif search_by == "sample":
                qs = qs.filter(booking__sample_name__name__icontains=search)
            else:
                qs = qs.filter(booking__sample_reg_no__icontains=search)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "").strip()
        context["search_by"] = self.request.GET.get("search_by", "sample_reg").strip()
        context["show_saved_popup"] = self.request.GET.get("saved") == "1"
        context["saved_booking_id"] = self.request.GET.get("booking_id", "").strip()
        return context


class ReportCreateOrUpdateView(PermissionRequiredMixin, RoleRequiredMixin, UpdateView):
    permission_required = "reports.change_report"
    required_roles = ("Manager", "Analyst", "Admin")
    model = Report
    form_class = ReportApprovalForm
    template_name = "reports/report_approval.html"

    def get_object(self, queryset=None):
        booking = get_object_or_404(Booking, pk=self.kwargs["booking_pk"])
        if booking.status != Booking.Status.APPROVED:
            raise Http404("Only approved bookings can generate report workflow.")
        report, _ = Report.objects.get_or_create(booking=booking, defaults={"created_by": self.request.user})
        return report

    def form_valid(self, form):
        if not (self.request.user.is_superuser or has_role(self.request.user, "Manager")):
            messages.error(self.request, "Only Manager can approve report workflow.")
            return self.form_invalid(form)

        report = form.save(commit=False)
        analysis_start_date = form.cleaned_data.get("analysis_start_date")
        analysis_end_date = form.cleaned_data.get("analysis_end_date")

        incharge_user = User.objects.filter(groups__name="Incharge", is_active=True).order_by("id").first()
        if not incharge_user:
            messages.error(self.request, "No active Incharge user found. Please create one in group Incharge.")
            return self.form_invalid(form)

        report.booking.analysis_start_date = analysis_start_date
        report.booking.analysis_end_date = analysis_end_date
        report.booking.save(update_fields=["analysis_start_date", "analysis_end_date"])
        report.analysis_end_date = analysis_end_date
        report.save(update_fields=["analysis_end_date", "updated_at"])
        report.approve_by_manager(self.request.user, incharge_user)
        messages.success(self.request, "Report approved by manager and auto-approved by incharge.")
        return redirect("reports:coa_edit", pk=report.pk)


class COAEditView(PermissionRequiredMixin, RoleRequiredMixin, UpdateView):
    permission_required = "reports.change_report"
    required_roles = ("Manager", "Incharge", "Analyst")
    model = Report
    form_class = COAEditForm
    template_name = "reports/coa_edit.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status != Report.Status.INCHARGE_APPROVED:
            messages.error(request, "COA can be edited only after manager approval and incharge auto-approval.")
            return redirect("reports:approval", booking_pk=self.object.booking_id)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_success_url(self):
        return (
            f"{reverse('reports:list')}?saved=1&booking_id={self.object.booking.tracking_code}"
        )


class COAPrintView(PermissionRequiredMixin, RoleRequiredMixin, DetailView):
    permission_required = "reports.view_report"
    required_roles = ("Manager", "Incharge", "Analyst")
    model = Report
    template_name = "reports/coa_print.html"
    context_object_name = "report"

    def get_context_data(self, **kwargs):
        """Populate flags that the template uses for rendering.

        Query parameters are used so that links in the UI can toggle
        between plain/letterhead versions and between COA/test report.
        """
        context = super().get_context_data(**kwargs)
        q = self.request.GET
        context["preview_mode"] = True
        context["auto_print"] = q.get("autoprint") == "1"
        context["is_plain_doc"] = q.get("plain") == "1"
        # letterhead querystring is treated as truthy when equal to '1'
        context["is_letterhead"] = q.get("letterhead") == "1"
        # the special `doc=test` flag switches to a test report layout
        context["is_test_report"] = q.get("doc") == "test"
        # the title shown at the top of the document
        context["document_title"] = "Test Report" if context["is_test_report"] else "Certificate of Analysis"
        context["letterhead_background"] = "img/test.jpeg" if context["is_test_report"] else "img/coa.jpeg"
        # build the url used by the QR code generator (mirrors the currently
        # requested view so it works for either COA or test report)
        base = reverse("reports:coa_print", kwargs={"pk": self.object.pk})
        if context["is_test_report"]:
            base += "?doc=test"
        if context["is_plain_doc"]:
            base += "&plain=1" if "?" in base else "?plain=1"
        context["coa_public_url"] = self.request.build_absolute_uri(base)
        context["qr_payload"] = context["coa_public_url"]
        context.update(_build_report_date_context(self.object))
        return context


class COAPlainDocumentView(PermissionRequiredMixin, RoleRequiredMixin, TemplateView):
    permission_required = "reports.view_report"
    required_roles = ("Manager", "Incharge", "Analyst")
    template_name = "reports/coa_doc.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = get_object_or_404(Report, pk=self.kwargs["pk"])
        context["report"] = report
        context["preview_mode"] = False
        context["auto_print"] = False
        context["is_plain_doc"] = self.request.GET.get("plain") == "1"
        context["is_test_report"] = self.request.GET.get("doc") == "test"
        context["document_title"] = "Test Report" if context["is_test_report"] else "Certificate of Analysis"
        context["letterhead_background"] = "img/test.jpeg" if context["is_test_report"] else "img/coa.jpeg"
        base = reverse("reports:coa_print", kwargs={"pk": report.pk})
        if context["is_test_report"]:
            base += "?doc=test"
        if context["is_plain_doc"]:
            base += "&plain=1" if "?" in base else "?plain=1"
        context["coa_public_url"] = self.request.build_absolute_uri(base)
        context["qr_payload"] = context["coa_public_url"]
        context.update(_build_report_date_context(report))
        return context


class COAPDFView(PermissionRequiredMixin, RoleRequiredMixin, RedirectView):
    permission_required = "reports.view_report"
    required_roles = ("Manager", "Incharge", "Analyst")
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        return reverse("reports:coa_print", kwargs={"pk": kwargs["pk"]})
