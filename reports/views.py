from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView, TemplateView, UpdateView

from bookings.models import Booking
from bookings.permissions import RoleRequiredMixin, has_role

from .forms import COAEditForm, ReportApprovalForm
from .models import Report


class ReportListView(PermissionRequiredMixin, RoleRequiredMixin, ListView):
    permission_required = "reports.view_report"
    required_roles = ("Manager", "Incharge", "Analyst")
    model = Report
    template_name = "reports/report_list.html"
    context_object_name = "reports"
    paginate_by = 10
    queryset = Report.objects.select_related("booking", "manager", "incharge").order_by("-created_at")


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
        manager_user = self.request.user
        analysis_start_date = form.cleaned_data.get("analysis_start_date")
        report_end_date = form.cleaned_data.get("report_end_date")

        report.booking.analysis_start_date = analysis_start_date
        report.booking.analysis_end_date = report_end_date
        report.booking.save(update_fields=["analysis_start_date", "analysis_end_date"])
        report.analysis_end_date = report_end_date
        report.save(update_fields=["analysis_end_date", "updated_at"])
        report.approve_by_manager(manager_user)
        messages.success(self.request, "Confirmed. COA edit opened. Edit only Result of Analysis section.")
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

    def get_success_url(self):
        messages.success(self.request, "COA content saved.")
        return reverse("reports:coa_edit", kwargs={"pk": self.object.pk})


class COAPrintView(PermissionRequiredMixin, RoleRequiredMixin, DetailView):
    permission_required = "reports.view_report"
    required_roles = ("Manager", "Incharge", "Analyst")
    model = Report
    template_name = "reports/coa_print.html"
    context_object_name = "report"


class COAPlainDocumentView(PermissionRequiredMixin, RoleRequiredMixin, TemplateView):
    permission_required = "reports.view_report"
    required_roles = ("Manager", "Incharge", "Analyst")
    template_name = "reports/coa_doc.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["report"] = get_object_or_404(Report, pk=self.kwargs["pk"])
        return context
