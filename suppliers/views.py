from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Supplier


@login_required
def supplier_list(request):
    search = request.GET.get('search', '')
    suppliers = Supplier.objects.filter(company=request.company).order_by('-created_at')
    if search:
        suppliers = suppliers.filter(name__icontains=search) | \
                    suppliers.filter(phone__icontains=search)
    return render(request, 'suppliers/supplier_list.html', {
        'suppliers': suppliers, 'search': search
    })


@login_required
def supplier_add(request):
    if request.method == 'POST':
        name       = request.POST.get('name')
        phone      = request.POST.get('phone')
        email      = request.POST.get('email')
        address    = request.POST.get('address')
        tax_number = request.POST.get('tax_number')
        notes      = request.POST.get('notes')
        if not name:
            messages.error(request, 'Supplier name is required.')
            return render(request, 'suppliers/supplier_form.html', {'action': 'Add'})
        Supplier.objects.create(
            company=request.company,
            name=name, phone=phone, email=email,
            address=address, tax_number=tax_number, notes=notes
        )
        messages.success(request, f'Supplier {name} added!')
        return redirect('supplier_list')
    return render(request, 'suppliers/supplier_form.html', {'action': 'Add'})


@login_required
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk, company=request.company)
    if request.method == 'POST':
        supplier.name       = request.POST.get('name')
        supplier.phone      = request.POST.get('phone')
        supplier.email      = request.POST.get('email')
        supplier.address    = request.POST.get('address')
        supplier.tax_number = request.POST.get('tax_number')
        supplier.notes      = request.POST.get('notes')
        supplier.save()
        messages.success(request, f'Supplier {supplier.name} updated!')
        return redirect('supplier_list')
    return render(request, 'suppliers/supplier_form.html', {
        'action': 'Edit', 'supplier': supplier
    })


@login_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk, company=request.company)
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, 'Supplier deleted.')
        return redirect('supplier_list')
    return render(request, 'suppliers/supplier_confirm_delete.html', {
        'supplier': supplier
    })