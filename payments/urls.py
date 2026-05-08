from django.urls import path
from . import views

urlpatterns = [
    path('', views.payment_list, name='payment_list'),
    path('add/', views.payment_add, name='payment_add'),
    path('delete/<int:pk>/', views.payment_delete, name='payment_delete'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
]