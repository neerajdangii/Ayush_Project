from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from django.conf.urls.static import static

from bookings.views import DashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^js/(?P<path>.*)$', serve, {'document_root': settings.BASE_DIR / 'public' / 'js'}),
    path('accounts/', include('accounts.urls')),
    path('bookings/', include('bookings.urls')),
    path('reports/', include('reports.urls')),
    path('', DashboardView.as_view(), name='dashboard'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')
