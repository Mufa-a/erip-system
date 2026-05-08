from django.urls import path
from . import views
from .admin_views import superadmin_dashboard

urlpatterns = [
    path('', views.billing_dashboard, name='billing_dashboard'),
    path('plans/', views.choose_plan, name='choose_plan'),
    path('superadmin/', superadmin_dashboard, name='superadmin_dashboard'),
]