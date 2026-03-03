from django.urls import path

from .views import COAEditView, COAPlainDocumentView, COAPrintView, ReportCreateOrUpdateView, ReportListView

app_name = "reports"

urlpatterns = [
    path("", ReportListView.as_view(), name="list"),
    path("booking/<int:booking_pk>/", ReportCreateOrUpdateView.as_view(), name="approval"),
    path("<int:pk>/coa/edit/", COAEditView.as_view(), name="coa_edit"),
    path("<int:pk>/coa/print/", COAPrintView.as_view(), name="coa_print"),
    path("<int:pk>/coa/doc/", COAPlainDocumentView.as_view(), name="coa_doc"),
]
