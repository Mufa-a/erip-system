from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import StockMovement
from products.models import Product


@login_required
def inventory_list(request):
    products = Product.objects.filter(
        company=request.company          # ✅ filter by company
    ).order_by('name')
    return render(request, 'inventory/inventory_list.html', {'products': products})


@login_required
def stock_movement(request):
    products  = Product.objects.filter(
        is_active=True, company=request.company  # ✅ filter by company
    )
    movements = StockMovement.objects.select_related(
        'product', 'created_by'
    ).filter(
        product__company=request.company         # ✅ filter movements by company
    ).order_by('-created_at')[:50]

    if request.method == 'POST':
        product_id    = request.POST.get('product')
        movement_type = request.POST.get('movement_type')
        quantity      = int(request.POST.get('quantity', 0))
        notes         = request.POST.get('notes', '')
        reference     = request.POST.get('reference', '')

        product = get_object_or_404(Product, pk=product_id, company=request.company)  # ✅

        StockMovement.objects.create(
            product=product,
            movement_type=movement_type,
            quantity=quantity,
            notes=notes,
            reference=reference,
            created_by=request.user
        )

        if movement_type in ('in', 'return'):
            product.stock += quantity
        elif movement_type == 'out':
            product.stock = max(0, product.stock - quantity)
        elif movement_type == 'adjust':
            product.stock = quantity

        product.save()
        messages.success(request, f'Stock updated for {product.name}!')
        return redirect('stock_movement')

    return render(request, 'inventory/stock_movement.html', {
        'products': products,
        'movements': movements,
    })