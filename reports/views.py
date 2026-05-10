from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth, TruncDate
from django.utils import timezone
from customers.models import Customer
from products.models import Product
from sales.models import Invoice
from payments.models import Payment
import json


@login_required
def dashboard(request):
    company = request.company

    # Auto-mark overdue invoices
    Invoice.objects.filter(
        due_date__lt=timezone.now().date()
    ).exclude(
        status__in=['paid', 'cancelled']
    ).update(status='overdue')

    # Filter by company
    if company:
        invoices  = Invoice.objects.filter(company=company)
        customers = Customer.objects.filter(company=company)
        products  = Product.objects.filter(company=company)
        payments  = Payment.objects.filter(company=company)
    else:
        invoices  = Invoice.objects.all()
        customers = Customer.objects.all()
        products  = Product.objects.all()
        payments  = Payment.objects.all()

    total_revenue = payments.aggregate(t=Sum('amount'))['t'] or 0

    # This month revenue
    this_month = timezone.now().replace(day=1)
    month_revenue = payments.filter(
        created_at__gte=this_month
    ).aggregate(t=Sum('amount'))['t'] or 0

    # Unpaid invoices total
    unpaid_total = sum(
        inv.balance_due for inv in invoices.exclude(status='paid')
    )

    context = {
        'total_customers':  customers.count(),
        'total_invoices':   invoices.count(),
        'total_products':   products.count(),
        'total_revenue':    f"{total_revenue:,.2f}",
        'month_revenue':    f"{month_revenue:,.2f}",
        'unpaid_total':     f"{unpaid_total:,.2f}",
        'paid_count':       invoices.filter(status='paid').count(),
        'unpaid_count':     invoices.exclude(status='paid').count(),
        'overdue_count':    invoices.filter(status='overdue').count(),
        'low_stock':        products.filter(stock__lte=10),
        'recent_invoices':  invoices.select_related('customer').order_by('-created_at')[:5],
        'recent_payments':  payments.select_related('invoice__customer').order_by('-created_at')[:5],
    }
    return render(request, 'dashboard.html', context)


@login_required
def reports(request):
    company = request.company

    if company:
        payments_qs  = Payment.objects.filter(company=company)
        invoices_qs  = Invoice.objects.filter(company=company)
        customers_qs = Customer.objects.filter(company=company)  # ✅
        products_qs  = Product.objects.filter(company=company)   # ✅
    else:
        payments_qs  = Payment.objects.all()
        invoices_qs  = Invoice.objects.all()
        customers_qs = Customer.objects.all()                     # ✅
        products_qs  = Product.objects.all()                      # ✅

    # Monthly revenue - last 6 months
    six_months_ago = timezone.now() - timezone.timedelta(days=180)
    monthly_payments = (
        payments_qs
        .filter(created_at__gte=six_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    monthly_labels = [p['month'].strftime('%b %Y') for p in monthly_payments]
    monthly_data   = [float(p['total']) for p in monthly_payments]

    # Invoice status breakdown
    status_data   = invoices_qs.values('status').annotate(count=Count('id'))
    status_labels = [s['status'].title() for s in status_data]
    status_counts = [s['count'] for s in status_data]

    # Top 5 products by sales
    from sales.models import InvoiceItem
    top_products = (
        InvoiceItem.objects
        .filter(invoice__company=company) if company else
        InvoiceItem.objects.all()
    )
    top_products = (
        top_products
        .values('product__name')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:5]
    )
    top_product_labels = [p['product__name'] for p in top_products]
    top_product_data   = [p['total_sold'] for p in top_products]

    # Daily revenue - last 7 days
    seven_days_ago = timezone.now() - timezone.timedelta(days=7)
    daily_payments = (
        payments_qs
        .filter(created_at__gte=seven_days_ago)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(total=Sum('amount'))
        .order_by('day')
    )
    daily_labels = [p['day'].strftime('%a %d') for p in daily_payments]
    daily_data   = [float(p['total']) for p in daily_payments]

    total_revenue   = payments_qs.aggregate(t=Sum('amount'))['t'] or 0
    paid_invoices   = invoices_qs.filter(status='paid').count()
    unpaid_invoices = invoices_qs.exclude(status='paid').count()

    context = {
        'monthly_labels':     json.dumps(monthly_labels),
        'monthly_data':       json.dumps(monthly_data),
        'status_labels':      json.dumps(status_labels),
        'status_counts':      json.dumps(status_counts),
        'top_product_labels': json.dumps(top_product_labels),
        'top_product_data':   json.dumps(top_product_data),
        'daily_labels':       json.dumps(daily_labels),
        'daily_data':         json.dumps(daily_data),
        'total_revenue':      f"{total_revenue:,.2f}",
        'paid_invoices':      paid_invoices,
        'unpaid_invoices':    unpaid_invoices,
        'total_customers':    customers_qs.count(),  # ✅ fixed
        'total_products':     products_qs.count(),   # ✅ fixed
    }
    return render(request, 'reports/reports.html', context)