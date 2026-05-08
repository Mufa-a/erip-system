from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Category


@login_required
def product_list(request):
    search = request.GET.get('search', '')
    products = Product.objects.select_related('category').order_by('-created_at')

    # ✅ FIX 1: filter by company
    if request.company:
        products = products.filter(company=request.company)

    if search:
        products = products.filter(name__icontains=search) | \
                   products.filter(sku__icontains=search)
    return render(request, 'products/product_list.html', {
        'products': products,
        'search': search
    })


@login_required
def product_add(request):
    # ✅ FIX 2: filter categories by company
    categories = Category.objects.filter(company=request.company)

    if request.method == 'POST':
        name            = request.POST.get('name')
        sku             = request.POST.get('sku')
        price           = request.POST.get('price')
        cost_price      = request.POST.get('cost_price')
        stock           = request.POST.get('stock')
        category_id     = request.POST.get('category')
        description     = request.POST.get('description')
        low_stock_alert = request.POST.get('low_stock_alert', 10)

        if not name or not sku or not price:
            messages.error(request, 'Name, SKU and price are required.')
            return render(request, 'products/product_form.html', {
                'action': 'Add', 'categories': categories
            })

        category = Category.objects.filter(pk=category_id).first()
        Product.objects.create(
            company=request.company,  # ✅ FIX 3: assign company on create
            name=name, sku=sku, price=price,
            cost_price=cost_price, stock=stock,
            category=category, description=description,
            low_stock_alert=low_stock_alert
        )
        messages.success(request, f'Product {name} added successfully!')
        return redirect('product_list')

    return render(request, 'products/product_form.html', {
        'action': 'Add', 'categories': categories
    })


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, company=request.company)
    categories = Category.objects.filter(company=request.company)

    if request.method == 'POST':
        product.name            = request.POST.get('name')
        product.sku             = request.POST.get('sku')
        product.price           = request.POST.get('price')
        product.cost_price      = request.POST.get('cost_price')
        product.stock           = request.POST.get('stock')
        product.description     = request.POST.get('description')
        product.low_stock_alert = request.POST.get('low_stock_alert', 10)
        category_id             = request.POST.get('category')
        product.category        = Category.objects.filter(pk=category_id).first()
        product.save()
        messages.success(request, f'Product {product.name} updated!')
        return redirect('product_list')

    return render(request, 'products/product_form.html', {
        'action': 'Edit',
        'product': product,
        'categories': categories
    })


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, company=request.company)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'Product {name} deleted.')
        return redirect('product_list')
    return render(request, 'products/product_confirm_delete.html', {
        'product': product
    })


@login_required
def category_list(request):
    categories = Category.objects.filter(company=request.company)
    return render(request, 'products/category_list.html', {
        'categories': categories
    })


@login_required
def category_add(request):
    if request.method == 'POST':
        name        = request.POST.get('name')
        description = request.POST.get('description')
        if not name:
            messages.error(request, 'Category name is required.')
            return render(request, 'products/category_form.html')
        Category.objects.create(
            company=request.company,  # ✅ assign company to category too
            name=name,
            description=description
        )
        messages.success(request, f'Category {name} added!')
        return redirect('category_list')
    return render(request, 'products/category_form.html')