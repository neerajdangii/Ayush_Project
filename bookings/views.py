from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.db.models import Count, Q
from django.http import JsonResponse
from django.http.response import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from reports.models import Report, ReportRemark, ReportTemplate

from .forms import (
    BookingForm,
    CustomerMasterForm,
    ManufacturerMasterForm,
    ProtocolMasterForm,
    ReportRemarkMasterForm,
    SampleNameMasterForm,
    SubmitterMasterForm,
    TestMasterForm,
    UOMMasterForm,
)
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
from .permissions import RoleRequiredMixin


MASTER_CONFIG = {
    "customer": {
        "model": CustomerMaster,
        "form": CustomerMasterForm,
        "title": "Customer Master",
        "detail_attr": "address",
    },
    "submitter": {"model": SubmitterMaster, "form": SubmitterMasterForm, "title": "Submitter Master"},
    "manufacturer": {"model": ManufacturerMaster, "form": ManufacturerMasterForm, "title": "Manufacturer Master"},
    "sample-name": {"model": SampleNameMaster, "form": SampleNameMasterForm, "title": "Sample Name Master"},
    "test": {"model": TestMaster, "form": TestMasterForm, "title": "Test Master"},
    "protocol": {"model": ProtocolMaster, "form": ProtocolMasterForm, "title": "Protocol Master"},
    "uom": {"model": UOMMaster, "form": UOMMasterForm, "title": "UOM Master"},
    "remark": {
        "model": ReportRemark,
        "form": ReportRemarkMasterForm,
        "title": "Remark Master",
        "order_by": ("sort_order", "title"),
        "primary_attr": "title",
        "detail_attr": "content",
    },
}
INLINE_ALLOWED_MASTERS = {"customer", "submitter", "manufacturer", "sample-name", "test"}


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["counts"] = Booking.objects.values("status").annotate(total=Count("id"))
        context["reports_total"] = Report.objects.count()
        context["report_templates_total"] = ReportTemplate.objects.count()
        context["masters"] = [
            {"slug": slug, "title": conf["title"], "count": conf["model"].objects.count()}
            for slug, conf in MASTER_CONFIG.items()
        ]
        return context


class BookingCreateView(RoleRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "bookings.add_booking"
    required_roles = ("Analyst", "Admin")
    model = Booking
    form_class = BookingForm
    template_name = "bookings/booking_form.html"
    success_url = reverse_lazy("bookings:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        duplicate_id = self.request.GET.get("duplicate")
        context["duplicate_id"] = duplicate_id
        context["edit_mode"] = False
        context["inline_master_slugs"] = INLINE_ALLOWED_MASTERS
        return context

    def get_initial(self):
        initial = super().get_initial()
        duplicate_id = self.request.GET.get("duplicate")
        if duplicate_id:
            source = get_object_or_404(Booking, pk=duplicate_id)
            initial.update(
                {
                    "booking_date": source.booking_date,
                    "letter_date": source.letter_date,
                    "sampling_upto": source.sampling_upto,
                    "sample_receipt_date": source.sample_receipt_date,
                    "customer": source.customer_id,
                    "submitter": source.submitter_id,
                    "manufacturer": source.manufacturer_id,
                    "sample_name": source.sample_name_id,
                    "sample_type": source.sample_type,
                    "protocol": source.protocol_id,
                    "uom": source.uom_id,
                    "booking_type": source.booking_type,
                    "sample_qty": source.sample_qty,
                    "sample_location": source.sample_location,
                    "packaging_mode": source.packaging_mode,
                    "sample_condition": source.sample_condition,
                    "batch_no": source.batch_no,
                    "batch_size": source.batch_size,
                    "manufacture_date": source.manufacture_date,
                    "expiry_retest_date": source.expiry_retest_date,
                    "license_no": source.license_no,
                    "collected_by_name": source.collected_by_name,
                    "sampling_procedure": source.sampling_procedure,
                    "analysis_start_date": source.analysis_start_date,
                    "analysis_end_date": source.analysis_end_date,
                    "remarks": source.remarks,
                    "test_to_be_performed": list(source.test_to_be_performed.values_list("id", flat=True)),
                }
            )
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        try:
            response = super().form_valid(form)
        except DatabaseError:
            messages.error(
                self.request,
                "Database schema is not up to date. Please run migrations and try again.",
            )
            return redirect("bookings:create")
        duplicate_id = self.request.GET.get("duplicate")
        if duplicate_id:
            messages.success(self.request, "Booking duplicated successfully. You can edit and save.")
        else:
            messages.success(self.request, "Booking created successfully.")
        messages.info(self.request, f"Booking ID: {self.object.tracking_code}. Copy this ID to search quickly.")
        return response


class BookingUpdateView(RoleRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "bookings.change_booking"
    required_roles = ("Analyst", "Admin", "Manager")
    model = Booking
    form_class = BookingForm
    template_name = "bookings/booking_form.html"
    success_url = reverse_lazy("bookings:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["duplicate_id"] = None
        context["edit_mode"] = True
        context["inline_master_slugs"] = INLINE_ALLOWED_MASTERS
        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except DatabaseError:
            messages.error(
                self.request,
                "Database schema is not up to date. Please run migrations and try again.",
            )
            return redirect("bookings:list")
        messages.success(self.request, "Booking updated successfully.")
        messages.info(self.request, f"Booking ID: {self.object.tracking_code}. Copy this ID to search quickly.")
        return response


class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = "bookings/booking_list.html"
    context_object_name = "bookings"
    paginate_by = 10

    def get_queryset(self):
        qs = (
            Booking.objects.select_related("customer", "sample_name", "created_by")
            .prefetch_related("test_to_be_performed")
            .order_by("-created_at")
        )
        search = self.request.GET.get("q", "").strip()
        search_by = self.request.GET.get("search_by", "sample_reg_no").strip()
        if search:
            if search_by == "customer":
                qs = qs.filter(customer__name__icontains=search)
            elif search_by == "sample":
                qs = qs.filter(sample_name__name__icontains=search)
            elif search_by == "batch_no":
                qs = qs.filter(batch_no__iexact=search)
            elif search_by == "tracking":
                qs = qs.filter(tracking_code__iexact=search)
            else:
                qs = qs.filter(sample_reg_no__icontains=search)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        context["search_by"] = self.request.GET.get("search_by", "sample_reg_no").strip()
        return context


class BookingApproveView(RoleRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "bookings.change_booking"
    required_roles = ("Manager", "Admin")

    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        if booking.status == Booking.Status.APPROVED:
            messages.info(request, "Booking is already approved.")
            return redirect("bookings:list")
        booking.approve(request.user)
        messages.success(request, "Booking approved.")
        return redirect("bookings:list")


class MasterListView(LoginRequiredMixin, TemplateView):
    template_name = "bookings/master_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs["slug"]
        conf = MASTER_CONFIG.get(slug)
        if not conf:
            raise Http404("Invalid master type")
        order_by = conf.get("order_by", ("name",))
        queryset = conf["model"].objects.order_by(*order_by)
        paginator = Paginator(queryset, 20)
        page_obj = paginator.get_page(self.request.GET.get("page"))
        primary_attr = conf.get("primary_attr", "name")
        detail_attr = conf.get("detail_attr")
        rows = []
        for obj in page_obj.object_list:
            rows.append(
                {
                    "object": obj,
                    "primary": getattr(obj, primary_attr, ""),
                    "detail": getattr(obj, detail_attr, "") if detail_attr else "",
                    "created_at": getattr(obj, "created_at", None),
                }
            )
        context.update(
            {
                "master_slug": slug,
                "title": conf["title"],
                "page_obj": page_obj,
                "object_list": page_obj.object_list,
                "rows": rows,
                "can_inline": slug in INLINE_ALLOWED_MASTERS,
            }
        )
        return context


class MasterCreateView(RoleRequiredMixin, PermissionRequiredMixin, CreateView):
    required_roles = ("Admin",)
    permission_required = "bookings.add_customermaster"
    template_name = "bookings/master_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.slug = kwargs["slug"]
        conf = MASTER_CONFIG.get(self.slug)
        if not conf:
            raise Http404("Invalid master type")
        self.model = conf["model"]
        self.form_class = conf["form"]
        self.title = conf["title"]
        self.permission_required = f"{self.model._meta.app_label}.add_{self.model._meta.model_name}"
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Add {self.title}"
        context["master_slug"] = self.slug
        return context

    def get_success_url(self):
        messages.success(self.request, f"{self.title} added.")
        return reverse("bookings:master_list", kwargs={"slug": self.slug})


class MasterUpdateView(RoleRequiredMixin, PermissionRequiredMixin, UpdateView):
    required_roles = ("Admin",)
    permission_required = "bookings.change_customermaster"
    template_name = "bookings/master_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.slug = kwargs["slug"]
        conf = MASTER_CONFIG.get(self.slug)
        if not conf:
            raise Http404("Invalid master type")
        self.model = conf["model"]
        self.form_class = conf["form"]
        self.title = conf["title"]
        self.permission_required = f"{self.model._meta.app_label}.change_{self.model._meta.model_name}"
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Edit {self.title}"
        context["master_slug"] = self.slug
        return context

    def get_success_url(self):
        messages.success(self.request, f"{self.title} updated.")
        return reverse("bookings:master_list", kwargs={"slug": self.slug})


class MasterDeleteView(RoleRequiredMixin, PermissionRequiredMixin, DeleteView):
    required_roles = ("Admin",)
    permission_required = "bookings.delete_customermaster"
    template_name = "bookings/master_confirm_delete.html"

    def dispatch(self, request, *args, **kwargs):
        self.slug = kwargs["slug"]
        conf = MASTER_CONFIG.get(self.slug)
        if not conf:
            raise Http404("Invalid master type")
        self.model = conf["model"]
        self.title = conf["title"]
        self.permission_required = f"{self.model._meta.app_label}.delete_{self.model._meta.model_name}"
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Delete {self.title}"
        context["master_slug"] = self.slug
        return context

    def get_success_url(self):
        messages.success(self.request, f"{self.title} deleted.")
        return reverse("bookings:master_list", kwargs={"slug": self.slug})


class InlineMasterCreateView(RoleRequiredMixin, View):
    required_roles = ("Analyst", "Admin")

    def post(self, request, slug):
        if slug not in INLINE_ALLOWED_MASTERS:
            return JsonResponse({"error": "Inline add is not allowed for this master."}, status=400)

        conf = MASTER_CONFIG[slug]
        name = request.POST.get("name", "").strip()
        if not name:
            return JsonResponse({"error": "Name is required."}, status=400)

        defaults = {"is_active": True}
        if slug == "customer":
            defaults["address"] = request.POST.get("address", "").strip()

        obj, created = conf["model"].objects.get_or_create(name=name, defaults=defaults)
        if not obj.is_active:
            obj.is_active = True
            obj.save(update_fields=["is_active"])

        return JsonResponse(
            {
                "id": obj.pk,
                "name": obj.name,
                "address": getattr(obj, "address", ""),
                "created": created,
            }
        )


def create_default_roles():
    from django.contrib.auth.models import Group

    for role in ("Admin", "Manager", "Incharge", "Analyst"):
        Group.objects.get_or_create(name=role)
