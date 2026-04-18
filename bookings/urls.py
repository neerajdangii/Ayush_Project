from django.urls import path

from .views import (
    BookingApproveView,
    BookingCreateView,
    BookingListView,
    BookingUpdateView,
    GetSimilarBookingDataView,
    InlineMasterCreateView,
    MasterCreateView,
    MasterDeleteView,
    MasterListView,
    MasterUpdateView,
)

app_name = "bookings"

urlpatterns = [
    path("", BookingListView.as_view(), name="list"),
    path("new/", BookingCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", BookingUpdateView.as_view(), name="edit"),
    path("<int:pk>/approve/", BookingApproveView.as_view(), name="approve"),
    path("api/similar-booking-data/", GetSimilarBookingDataView.as_view(), name="api_similar_booking_data"),
    path("masters/<slug:slug>/", MasterListView.as_view(), name="master_list"),
    path("masters/<slug:slug>/add/", MasterCreateView.as_view(), name="master_add"),
    path("masters/<slug:slug>/<int:pk>/edit/", MasterUpdateView.as_view(), name="master_edit"),
    path("masters/<slug:slug>/<int:pk>/delete/", MasterDeleteView.as_view(), name="master_delete"),
    path("masters/<slug:slug>/inline-create/", InlineMasterCreateView.as_view(), name="master_inline_create"),
]
