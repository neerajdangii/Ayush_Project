from django.urls import path

from .views import AdminUserCreateView, UserLoginView, UserLogoutView

app_name = 'accounts'

urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('users/new/', AdminUserCreateView.as_view(), name='create_user'),
]
