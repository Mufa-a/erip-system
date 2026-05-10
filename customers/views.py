from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Customer


@login_required
def customer_list(request):
    if not request.company:
        messages.error(request, 'You are not assigned to a company. Contact your administrator.')
        return redirect('dashboard')
    
    search = request.GET.get('search', '')
    customers = Customer.objects.filter(company=request.company).order_by('-created_at')
    if search:
        customers = customers.filter(name__icontains=search) | \
                    customers.filter(phone__icontains=search) | \
                    customers.filter(email__icontains=search)
    return render(request, 'customers/customer_list.html', {'customers': customers, 'search': search})


@login_required
def customer_add(request):
    if request.method == 'POST':
        name       = request.POST.get('name')
        email      = request.POST.get('email')
        phone      = request.POST.get('phone')
        address    = request.POST.get('address')
        city       = request.POST.get('city')
        tax_number = request.POST.get('tax_number')
        notes      = request.POST.get('notes')

        if not name or not phone:
            messages.error(request, 'Name and phone are required.')
            return render(request, 'customers/customer_form.html', {'action': 'Add'})

        Customer.objects.create(
            company=request.company,     # ✅ assign company on create
            name=name, email=email, phone=phone,
            address=address, city=city,
            tax_number=tax_number, notes=notes
        )
        messages.success(request, f'Customer {name} added successfully!')
        return redirect('customer_list')

    return render(request, 'customers/customer_form.html', {'action': 'Add'})


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk, company=request.company)  # ✅

    if request.method == 'POST':
        customer.name       = request.POST.get('name')
        customer.email      = request.POST.get('email')
        customer.phone      = request.POST.get('phone')
        customer.address    = request.POST.get('address')
        customer.city       = request.POST.get('city')
        customer.tax_number = request.POST.get('tax_number')
        customer.notes      = request.POST.get('notes')
        customer.save()
        messages.success(request, f'Customer {customer.name} updated!')
        return redirect('customer_list')

    return render(request, 'customers/customer_form.html', {
        'action': 'Edit',
        'customer': customer
    })


@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk, company=request.company)  # ✅

    if request.method == 'POST':
        if customer.invoices.exists():
            messages.error(
                request,
                f'Cannot delete {customer.name} — they have '
                f'{customer.invoices.count()} invoice(s). '
                f'Delete the invoices first or deactivate the customer instead.'
            )
            return redirect('customer_list')
        name = customer.name
        customer.delete()
        messages.success(request, f'Customer {name} deleted.')
        return redirect('customer_list')

    return render(request, 'customers/customer_confirm_delete.html', {
        'customer': customer
    })