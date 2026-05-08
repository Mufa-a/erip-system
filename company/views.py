from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Company, CompanyUser
from accounts.models import User


@login_required
def company_list(request):
    memberships = CompanyUser.objects.filter(
        user=request.user
    ).select_related('company')
    return render(request, 'company/company_list.html', {
        'memberships': memberships
    })


@login_required
def company_create(request):
    if request.method == 'POST':
        company = Company.objects.create(
            name       = request.POST.get('name'),
            email      = request.POST.get('email'),
            phone      = request.POST.get('phone'),
            address    = request.POST.get('address'),
            city       = request.POST.get('city'),
            tax_number = request.POST.get('tax_number'),
            currency   = request.POST.get('currency', 'KES'),
        )
        # Make creator the owner
        CompanyUser.objects.create(
            company=company,
            user=request.user,
            role=CompanyUser.Role.OWNER
        )
        request.session['company_id'] = company.id
        messages.success(request, f'Company {company.name} created!')
        return redirect('dashboard')

    return render(request, 'company/company_form.html')


@login_required
def company_switch(request, pk):
    membership = get_object_or_404(
        CompanyUser, company__pk=pk, user=request.user
    )
    request.session['company_id'] = membership.company.id
    messages.success(request, f'Switched to {membership.company.name}')
    return redirect('dashboard')


@login_required
def company_settings(request):
    if not request.company:
        return redirect('company_create')

    company = request.company
    if request.method == 'POST':
        company.name       = request.POST.get('name')
        company.email      = request.POST.get('email')
        company.phone      = request.POST.get('phone')
        company.address    = request.POST.get('address')
        company.city       = request.POST.get('city')
        company.tax_number = request.POST.get('tax_number')
        company.currency   = request.POST.get('currency', 'KES')
        if request.FILES.get('logo'):
            company.logo = request.FILES['logo']
        company.save()
        messages.success(request, 'Company settings updated!')
        return redirect('company_settings')

    return render(request, 'company/company_settings.html', {
        'company': company
    })


@login_required
def company_add_user(request):
    if not request.company:
        return redirect('company_create')

    if request.method == 'POST':
        username = request.POST.get('username')
        role     = request.POST.get('role')
        try:
            user = User.objects.get(username=username)
            CompanyUser.objects.get_or_create(
                company=request.company,
                user=user,
                defaults={'role': role}
            )
            messages.success(request, f'{username} added to company!')
        except User.DoesNotExist:
            messages.error(request, f'User {username} not found.')
        return redirect('company_settings')

    return redirect('company_settings')