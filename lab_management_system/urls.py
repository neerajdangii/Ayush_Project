from django.contrib import admin
from django.urls import include, path

from bookings.views import DashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('bookings/', include('bookings.urls')),
    path('reports/', include('reports.urls')),
    path('', DashboardView.as_view(), name='dashboard'),
]
