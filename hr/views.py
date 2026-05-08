from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Employee, Payroll
import datetime


@login_required
def employee_list(request):
    employees = Employee.objects.filter(company=request.company).order_by('first_name')
    return render(request, 'hr/employee_list.html', {'employees': employees})


@login_required
def employee_add(request):
    if request.method == 'POST':
        emp = Employee.objects.create(
            company         = request.company,
            employee_number = request.POST.get('employee_number'),
            first_name      = request.POST.get('first_name'),
            last_name       = request.POST.get('last_name'),
            email           = request.POST.get('email'),
            phone           = request.POST.get('phone'),
            id_number       = request.POST.get('id_number'),
            kra_pin         = request.POST.get('kra_pin'),
            nssf_number     = request.POST.get('nssf_number'),
            nhif_number     = request.POST.get('nhif_number'),
            department      = request.POST.get('department'),
            employment_type = request.POST.get('employment_type'),
            basic_salary    = request.POST.get('basic_salary'),
            hire_date       = request.POST.get('hire_date'),
        )
        messages.success(request, f'Employee {emp.full_name} added!')
        return redirect('employee_list')
    return render(request, 'hr/employee_form.html', {
        'action': 'Add',
        'departments': Employee.Department.choices,
        'employment_types': Employee.EmploymentType.choices,
    })


@login_required
def employee_edit(request, pk):
    emp = get_object_or_404(Employee, pk=pk, company=request.company)
    if request.method == 'POST':
        emp.first_name      = request.POST.get('first_name')
        emp.last_name       = request.POST.get('last_name')
        emp.email           = request.POST.get('email')
        emp.phone           = request.POST.get('phone')
        emp.id_number       = request.POST.get('id_number')
        emp.kra_pin         = request.POST.get('kra_pin')
        emp.nssf_number     = request.POST.get('nssf_number')
        emp.nhif_number     = request.POST.get('nhif_number')
        emp.department      = request.POST.get('department')
        emp.employment_type = request.POST.get('employment_type')
        emp.basic_salary    = request.POST.get('basic_salary')
        emp.hire_date       = request.POST.get('hire_date')
        emp.is_active       = request.POST.get('is_active') == 'on'
        emp.save()
        messages.success(request, f'Employee {emp.full_name} updated!')
        return redirect('employee_list')
    return render(request, 'hr/employee_form.html', {
        'action': 'Edit',
        'emp': emp,
        'departments': Employee.Department.choices,
        'employment_types': Employee.EmploymentType.choices,
    })


@login_required
def employee_delete(request, pk):
    emp = get_object_or_404(Employee, pk=pk, company=request.company)
    if request.method == 'POST':
        emp.delete()
        messages.success(request, 'Employee deleted.')
        return redirect('employee_list')
    return render(request, 'hr/employee_confirm_delete.html', {'emp': emp})


@login_required
def payroll_list(request):
    payrolls = Payroll.objects.filter(
        employee__company=request.company
    ).select_related('employee').order_by('-month')
    return render(request, 'hr/payroll_list.html', {'payrolls': payrolls})


@login_required
def payroll_generate(request):
    employees = Employee.objects.filter(company=request.company, is_active=True)
    if request.method == 'POST':
        employee_id      = request.POST.get('employee')
        month_str        = request.POST.get('month')
        allowances       = float(request.POST.get('allowances', 0))
        overtime         = float(request.POST.get('overtime', 0))
        other_deductions = float(request.POST.get('other_deductions', 0))
        notes            = request.POST.get('notes', '')

        emp   = get_object_or_404(Employee, pk=employee_id, company=request.company)
        month = datetime.datetime.strptime(month_str, '%Y-%m').date()

        payroll = Payroll(
            employee=emp,
            month=month,
            basic_salary=emp.basic_salary,
            allowances=allowances,
            overtime=overtime,
            other_deductions=other_deductions,
            notes=notes
        )
        payroll.calculate()
        payroll.save()

        messages.success(request, f'Payroll for {emp.full_name} generated!')
        return redirect('payroll_list')

    return render(request, 'hr/payroll_form.html', {
        'employees': employees,
        'today': timezone.now().strftime('%Y-%m'),
    })


@login_required
def payroll_detail(request, pk):
    payroll = get_object_or_404(Payroll, pk=pk, employee__company=request.company)
    if request.method == 'POST':
        payroll.status = request.POST.get('status')
        payroll.save()
        messages.success(request, 'Payroll status updated!')
        return redirect('payroll_detail', pk=pk)
    return render(request, 'hr/payroll_detail.html', {'payroll': payroll})


@login_required
def payslip_print(request, pk):
    payroll = get_object_or_404(Payroll, pk=pk, employee__company=request.company)
    return render(request, 'hr/payslip_print.html', {'payroll': payroll})