from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='login'), name='accounts_home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.user_add, name='user_add'),
    path('users/edit/<int:pk>/', views.user_edit, name='user_edit'),
    path('users/delete/<int:pk>/', views.user_delete, name='user_delete'),
    path('theme/toggle/', views.toggle_theme, name='toggle_theme'),
]