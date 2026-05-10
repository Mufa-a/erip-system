from django.contrib import admin
from .models import Company, CompanyUser, CompanySettings, SubscriptionPayment


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display  = ['name', 'email', 'phone', 'city', 'country', 'plan', 'is_active', 'created_at']
    list_filter   = ['plan', 'is_active', 'country']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['created_at']


@admin.register(CompanyUser)
class CompanyUserAdmin(admin.ModelAdmin):
    list_display  = ['user', 'company', 'role', 'is_active', 'created_at']
    list_filter   = ['role', 'is_active', 'company']
    search_fields = ['user__username', 'company__name']


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display  = ['company', 'has_hr', 'has_inventory', 'has_suppliers', 'has_accounting', 'has_reports']
    list_filter   = ['has_hr', 'has_inventory', 'has_accounting']


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display  = ['company', 'plan', 'amount', 'status', 'months_paid', 'reference', 'created_at']
    list_filter   = ['status', 'plan', 'company']
    search_fields = ['company__name', 'reference']
    readonly_fields = ['created_at']