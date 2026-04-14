from __future__ import annotations

from datetime import date, datetime, time
import re

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.http import JsonResponse
from django.http import HttpResponseServerError
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.http import HttpResponse
from django.template.defaultfilters import linebreaksbr
from django.template.loader import render_to_string
from django.utils.html import escape
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView
from django.utils.decorators import method_decorator

try:
    from weasyprint import HTML
except (ImportError, OSError):
    HTML = None

from bookings.models import Booking
from bookings.permissions import RoleRequiredMixin, has_role

from .forms import COAEditForm, ReportApprovalForm, ReportTemplateForm
from .models import Report, ReportRemark, ReportTemplate

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
        "report_letter_date": _format_report_date(booking.letter_date, include_time=False),
        "report_received_date": _format_report_date(booking.sample_receipt_date, include_time=False),
        "report_analysis_start_date": _format_report_date(booking.analysis_start_date, include_time=False),
        "report_analysis_end_date": _format_report_date(report.analysis_end_date, include_time=False),
        "report_manufacture_date": _format_report_date(booking.manufacture_date, month_year_only=True),
        "report_expiry_date": _format_report_date(booking.expiry_retest_date, month_year_only=True),
    }


def _get_report_render_context(report, request, *, preview_mode, auto_print, is_plain_doc, is_test_report):
    remark_text = (report.remark_text or "").strip()
    if not remark_text and report.selected_remark_id:
        remark_text = (report.selected_remark.content or "").strip()

    tail_html = '<div class="coa-end-report">*** END OF REPORT ***</div>'
    if remark_text:
        tail_html += f'<div class="coa-remark">Remark: {linebreaksbr(escape(remark_text))}</div>'

    context = {
        "report": report,
        "preview_mode": preview_mode,
        "auto_print": auto_print,
        "is_plain_doc": is_plain_doc,
        "is_test_report": is_test_report,
        "document_title": "Test Report" if is_test_report else "Certificate of Analysis",
        "tail_html": mark_safe(tail_html),
        "draft_remark_text": remark_text,
    }

    base = reverse("reports:coa_print", kwargs={"pk": report.pk})
    if is_test_report:
        base += "?doc=test"
    if is_plain_doc:
        base += "&plain=1" if "?" in base else "?plain=1"

    context["coa_public_url"] = request.build_absolute_uri(base)
    context["qr_payload"] = context["coa_public_url"]
    context["report_ceo_content"] = mark_safe(report.ceo_content or "")
    context.update(_build_report_date_context(report))
    return context


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

        def _to_day_start(value):
            if not value:
                return None
            dt = datetime.combine(value, time.min)
            return timezone.make_aware(dt, timezone.get_current_timezone()) if timezone.is_naive(dt) else dt

        analysis_start_date = _to_day_start(analysis_start_date)
        analysis_end_date = _to_day_start(analysis_end_date)

        report.booking.analysis_start_date = analysis_start_date
        report.booking.analysis_end_date = analysis_end_date
        report.booking.save(update_fields=["analysis_start_date", "analysis_end_date"])
        report.analysis_end_date = analysis_end_date
        report.save(update_fields=["analysis_end_date", "updated_at"])
        report.approve_by_manager(self.request.user)
        messages.success(self.request, "Report approved by manager.")
        return redirect("reports:coa_edit", pk=report.pk)


class COAEditView(PermissionRequiredMixin, RoleRequiredMixin, UpdateView):
    permission_required = "reports.change_report"
    required_roles = ("Manager", "Incharge", "Analyst")
    model = Report
    form_class = COAEditForm
    template_name = "reports/coa_edit.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        allowed_statuses = {
            Report.Status.MANAGER_APPROVED,
            Report.Status.INCHARGE_APPROVED,
        }
        if self.object.status not in allowed_statuses:
            messages.error(request, "COA can be edited only after report approval.")
            return redirect("reports:approval", booking_pk=self.object.booking_id)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        templates = ReportTemplate.objects.filter(is_active=True).select_related("sample_name", "protocol")
        previous_reports = Report.objects.none()
        sample_name_id = getattr(self.object.booking, "sample_name_id", None)
        if sample_name_id:
            previous_reports = (
                Report.objects.select_related("booking")
                .filter(booking__sample_name_id=sample_name_id)
                .exclude(pk=self.object.pk)
                .exclude(ceo_content="")
                .order_by("-updated_at", "-created_at")
            )
        context["remark_options"] = list(
            ReportRemark.objects.filter(is_active=True).values("id", "title", "content")
        )
        context["template_options"] = [
            {
                "id": template.pk,
                "name": template.name,
                "sample_name": template.sample_name.name if template.sample_name else "",
                "protocol": template.protocol.name if template.protocol else "",
            }
            for template in templates
        ]
        context["old_report_options"] = [
            {
                "id": report.pk,
                "sample_reg_no": report.booking.sample_reg_no,
                "certificate_no": report.certificate_no,
                "updated_at": timezone.localtime(report.updated_at).strftime("%d/%m/%Y %I:%M %p")
                if timezone.is_aware(report.updated_at)
                else report.updated_at.strftime("%d/%m/%Y %I:%M %p"),
            }
            for report in previous_reports[:20]
        ]
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
        q = self.request.GET
        context = _get_report_render_context(
            self.object,
            self.request,
            preview_mode=True,
            auto_print=q.get("autoprint") == "1",
            is_plain_doc=q.get("plain") == "1",
            is_test_report=q.get("doc") == "test",
        )
        context["is_letterhead"] = q.get("letterhead") == "1"
        return context


class COAPlainDocumentView(PermissionRequiredMixin, RoleRequiredMixin, TemplateView):
    permission_required = "reports.view_report"
    required_roles = ("Manager", "Incharge", "Analyst")
    template_name = "reports/coa_doc.html"

    def get_context_data(self, **kwargs):
        report = get_object_or_404(Report, pk=self.kwargs["pk"])
        return _get_report_render_context(
            report,
            self.request,
            preview_mode=False,
            auto_print=False,
            is_plain_doc=self.request.GET.get("plain") == "1",
            is_test_report=self.request.GET.get("doc") == "test",
        )


class COAPDFView(PermissionRequiredMixin, RoleRequiredMixin, DetailView):
    permission_required = "reports.view_report"
    required_roles = ("Manager", "Incharge", "Analyst")
    model = Report
    template_name = None

    def get(self, request, *args, **kwargs):
        report = self.get_object()

        if HTML is None:
            return HttpResponseServerError("PDF generation is unavailable because WeasyPrint system libraries are missing.")

        # Render HTML context
        context = self.get_context_data()
        html_string = render_to_string('reports/coa_doc.html', context, request=request)

        # Generate PDF
        html = HTML(string=html_string)
        pdf_bytes = html.write_pdf()

        # Return PDF response
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="COA_{report.booking.sample_reg_no}.pdf"'
        return response

    def get_context_data(self, **kwargs):
        report = self.object
        context = _get_report_render_context(
            report,
            self.request,
            preview_mode=False,
            auto_print=False,
            is_plain_doc=self.request.GET.get("plain") == "1",
            is_test_report=self.request.GET.get("doc") == "test",
        )
        return context


class ReportTemplateListView(PermissionRequiredMixin, RoleRequiredMixin, ListView):
    permission_required = "reports.view_reporttemplate"
    required_roles = ("Admin", "Manager", "Analyst")
    model = ReportTemplate
    template_name = "reports/report_template_list.html"
    context_object_name = "templates"

    def get_queryset(self):
        return ReportTemplate.objects.select_related("sample_name", "protocol").order_by("-is_default", "name")


class ReportTemplateCreateView(PermissionRequiredMixin, RoleRequiredMixin, CreateView):
    permission_required = "reports.add_reporttemplate"
    required_roles = ("Admin", "Manager")
    model = ReportTemplate
    form_class = ReportTemplateForm
    template_name = "reports/report_template_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Add Report Template"
        return context

    def get_success_url(self):
        messages.success(self.request, "Report template added.")
        return reverse("reports:template_list")


class ReportTemplateUpdateView(PermissionRequiredMixin, RoleRequiredMixin, UpdateView):
    permission_required = "reports.change_reporttemplate"
    required_roles = ("Admin", "Manager")
    model = ReportTemplate
    form_class = ReportTemplateForm
    template_name = "reports/report_template_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Edit Report Template"
        return context

    def get_success_url(self):
        messages.success(self.request, "Report template updated.")
        return reverse("reports:template_list")


class ReportTemplateDeleteView(PermissionRequiredMixin, RoleRequiredMixin, DeleteView):
    permission_required = "reports.delete_reporttemplate"
    required_roles = ("Admin", "Manager")
    model = ReportTemplate
    template_name = "reports/report_template_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Delete Report Template"
        return context

    def get_success_url(self):
        messages.success(self.request, "Report template deleted.")
        return reverse("reports:template_list")


class ReportTemplateContentView(PermissionRequiredMixin, RoleRequiredMixin, DetailView):
    permission_required = "reports.view_reporttemplate"
    required_roles = ("Admin", "Manager", "Analyst")
    model = ReportTemplate

    def get(self, request, *args, **kwargs):
        template = self.get_object()
        return JsonResponse(
            {
                "id": template.pk,
                "name": template.name,
                "content": template.content,
            }
        )


@method_decorator(require_http_methods(["GET"]), name="dispatch")
class ReportTemplateApiListView(PermissionRequiredMixin, RoleRequiredMixin, ListView):
    permission_required = "reports.view_reporttemplate"
    required_roles = ("Admin", "Manager", "Analyst")
    model = ReportTemplate

    def render_to_response(self, context, **response_kwargs):
        templates = context["object_list"]
        return JsonResponse(
            {
                "templates": [
                    {
                        "id": template.pk,
                        "name": template.name,
                        "description": template.description,
                        "content": template.content,
                        "sample_name": template.sample_name.name if template.sample_name else None,
                        "protocol": template.protocol.name if template.protocol else None,
                        "created_at": timezone.localtime(template.created_at).isoformat() if timezone.is_aware(template.created_at) else template.created_at.isoformat(),
                    }
                    for template in templates
                ]
            }
        )

    def get_queryset(self):
        return ReportTemplate.objects.filter(is_active=True).select_related("sample_name", "protocol").order_by("name")


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class ReportApiDetailView(PermissionRequiredMixin, RoleRequiredMixin, DetailView):
    permission_required = "reports.view_report"
    required_roles = ("Manager", "Incharge", "Analyst")
    model = Report

    def get(self, request, *args, **kwargs):
        report = self.get_object()
        return JsonResponse(self._serialize_report(report))

    def post(self, request, *args, **kwargs):
        report = self.get_object()
        if not request.user.has_perm("reports.change_report"):
            return JsonResponse({"detail": "You do not have permission to edit reports."}, status=403)

        html_content = request.POST.get("content", "")
        report_name = request.POST.get("name", "").strip()
        report.ceo_content = html_content
        report.save(update_fields=["ceo_content", "updated_at"])

        payload = self._serialize_report(report)
        if report_name:
            payload["report_name"] = report_name
        payload["saved"] = True
        return JsonResponse(payload)

    def _serialize_report(self, report):
        return {
            "id": report.pk,
            "report_name": report.booking.sample_reg_no if report.booking else f"Report {report.pk}",
            "content": report.ceo_content,
            "created_at": timezone.localtime(report.created_at).isoformat() if timezone.is_aware(report.created_at) else report.created_at.isoformat(),
            "updated_at": timezone.localtime(report.updated_at).isoformat() if timezone.is_aware(report.updated_at) else report.updated_at.isoformat(),
            "template_id": report.report_template_id,
            "booking_id": report.booking_id,
            "certificate_no": report.certificate_no,
        }
