from django.contrib import admin
from .models import Employee, Payroll

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_number', 'full_name', 'department', 'basic_salary', 'is_active')
    search_fields = ('first_name', 'last_name', 'employee_number')

@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month', 'net_salary', 'status')