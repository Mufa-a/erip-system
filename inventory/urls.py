from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_list, name='inventory_list'),
    path('movements/', views.stock_movement, name='stock_movement'),
]