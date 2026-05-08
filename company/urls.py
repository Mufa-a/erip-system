from django.urls import path
from . import views

urlpatterns = [
    path('', views.company_list, name='company_list'),
    path('create/', views.company_create, name='company_create'),
    path('switch/<int:pk>/', views.company_switch, name='company_switch'),
    path('settings/', views.company_settings, name='company_settings'),
    path('add-user/', views.company_add_user, name='company_add_user'),
]