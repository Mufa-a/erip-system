from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Invoice, InvoiceItem
from customers.models import Customer
from products.models import Product
import uuid


def generate_invoice_number():
    return str(uuid.uuid4()).split('-')[0].upper()


@login_required
def invoice_list(request):
    invoices = Invoice.objects.select_related('customer').order_by('-created_at')
    if request.company:
        invoices = invoices.filter(company=request.company)
    return render(request, 'sales/invoice_list.html', {'invoices': invoices})


@login_required
def invoice_create(request):
    customers = Customer.objects.all()
    products  = Product.objects.filter(is_active=True)

    if request.company:
        customers = customers.filter(company=request.company)
        products  = products.filter(company=request.company)

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        due_date    = request.POST.get('due_date')
        tax_rate    = request.POST.get('tax_rate', 16)
        discount    = request.POST.get('discount', 0)
        notes       = request.POST.get('notes', '')

        customer = get_object_or_404(Customer, pk=customer_id)

        invoice = Invoice.objects.create(
            invoice_number=generate_invoice_number(),
            customer=customer,
            created_by=request.user,
            due_date=due_date,
            tax_rate=tax_rate,
            discount=discount,
            notes=notes,
            company=request.company,
        )

        product_ids = request.POST.getlist('product_id')
        quantities  = request.POST.getlist('quantity')
        unit_prices = request.POST.getlist('unit_price')

        for pid, qty, price in zip(product_ids, quantities, unit_prices):
            if pid and qty and price:
                product = Product.objects.filter(pk=pid).first()
                if product:
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        product=product,
                        quantity=int(qty),
                        unit_price=price
                    )
                    # Auto-reduce stock
                    product.stock = max(0, product.stock - int(qty))
                    product.save()

        messages.success(request, f'Invoice {invoice.invoice_number} created!')

        # ✅ FIX: SMS block now correctly indented inside if POST
        try:
            from core.sms import send_invoice_sms
            if send_invoice_sms(invoice):
                messages.info(request, f'SMS sent to {invoice.customer.phone}!')
        except Exception:
            pass

        # Send email notification
        try:
            from core.email_utils import send_invoice_email
            if send_invoice_email(invoice):
                messages.info(request, f'Invoice email sent to {invoice.customer.email}')
        except Exception:
            pass

        return redirect('invoice_list')

    return render(request, 'sales/invoice_form.html', {
        'customers': customers,
        'products':  products,
        'today':     timezone.now().date(),
    })


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'sales/invoice_detail.html', {'invoice': invoice})


@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, 'Invoice deleted.')
        return redirect('invoice_list')
    return render(request, 'sales/invoice_confirm_delete.html', {'invoice': invoice})


@login_required
def invoice_print(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'sales/invoice_print.html', {'invoice': invoice})


@login_required
def invoice_send_email(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    from core.email_utils import send_invoice_email
    if not invoice.customer.email:
        messages.error(request, 'Customer has no email address.')
    elif send_invoice_email(invoice):
        messages.success(request, f'Invoice emailed to {invoice.customer.email}!')
    else:
        messages.error(request, 'Failed to send email. Check your email settings.')
    return redirect('invoice_detail', pk=pk)