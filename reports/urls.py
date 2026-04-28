from django.urls import path

from .views import (
    COAEditView,
    COAPDFView,
    COAPlainDocumentView,
    COAPrintView,
    PublicCOAPrintView,
    ReportTemplateCreateView,
    ReportTemplateApiListView,
    ReportTemplateContentView,
    ReportTemplateDeleteView,
    ReportTemplateListView,
    ReportTemplateUpdateView,
    ReportCreateOrUpdateView,
    ReportApiDetailView,
    ReportListView,
)

app_name = "reports"

urlpatterns = [
    path("", ReportListView.as_view(), name="list"),
    path("api/templates/", ReportTemplateApiListView.as_view(), name="template_api_list"),
    path("api/<int:pk>/", ReportApiDetailView.as_view(), name="report_api_detail"),
    path("templates/", ReportTemplateListView.as_view(), name="template_list"),
    path("templates/add/", ReportTemplateCreateView.as_view(), name="template_add"),
    path("templates/<int:pk>/content/", ReportTemplateContentView.as_view(), name="template_content"),
    path("templates/<int:pk>/edit/", ReportTemplateUpdateView.as_view(), name="template_edit"),
    path("templates/<int:pk>/delete/", ReportTemplateDeleteView.as_view(), name="template_delete"),
    path("booking/<int:booking_pk>/", ReportCreateOrUpdateView.as_view(), name="approval"),
    path("<int:pk>/coa/edit/", COAEditView.as_view(), name="coa_edit"),
    path("<int:pk>/coa/print/", COAPrintView.as_view(), name="coa_print"),
    path("public/<int:pk>/", PublicCOAPrintView.as_view(), name="coa_public"),
    path("<int:pk>/coa/doc/", COAPlainDocumentView.as_view(), name="coa_doc"),
    path("<int:pk>/coa/pdf/", COAPDFView.as_view(), name="coa_pdf"),
]
