from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from company.models import Company, SubscriptionPayment, CompanySettings

PLAN_PRICES = {
    'starter':    2000,
    'business':   5000,
    'enterprise': 12000,
}

PLAN_MAX_USERS = {
    'starter':    2,
    'business':   10,
    'enterprise': 9999,
}


@login_required
def billing_dashboard(request):
    company  = request.company
    payments = SubscriptionPayment.objects.filter(company=company).order_by('-created_at')
    return render(request, 'billing/dashboard.html', {
        'company':   company,
        'payments':  payments,
        'prices':    PLAN_PRICES,
    })


@login_required
def choose_plan(request):
    if request.method == 'POST':
        plan      = request.POST.get('plan')
        months    = int(request.POST.get('months', 1))
        reference = request.POST.get('reference', '')

        if plan not in PLAN_PRICES:
            messages.error(request, 'Invalid plan selected.')
            return redirect('choose_plan')

        amount = PLAN_PRICES[plan] * months

        # Record the payment
        payment = SubscriptionPayment.objects.create(
            company     = request.company,
            amount      = amount,
            plan        = plan,
            months_paid = months,
            reference   = reference,
            status      = 'paid',
            paid_at     = timezone.now(),
        )

        # Update company plan
        company = request.company
        company.plan      = plan
        company.max_users = PLAN_MAX_USERS[plan]

        # ✅ FIXED - Extend expiry using datetime not date
        base = max(timezone.now(), company.plan_expires or timezone.now())
        company.plan_expires = base + relativedelta(months=months)
        company.save()

        # Update module access based on plan
        settings_obj, _ = CompanySettings.objects.get_or_create(company=company)
        if plan == 'starter':
            settings_obj.has_hr         = False
            settings_obj.has_accounting = False
            settings_obj.has_reports    = False
        elif plan == 'business':
            settings_obj.has_hr         = True
            settings_obj.has_accounting = True
            settings_obj.has_reports    = True
        elif plan == 'enterprise':
            settings_obj.has_hr         = True
            settings_obj.has_accounting = True
            settings_obj.has_reports    = True
        settings_obj.save()

        messages.success(request, f'Plan upgraded to {plan.title()} until {company.plan_expires}!')
        return redirect('billing_dashboard')

    comparison = [
        ('Customers & Sales',    True,  True,  True),
        ('Products & Inventory', True,  True,  True),
        ('Invoices & Payments',  True,  True,  True),
        ('Suppliers',            True,  True,  True),
        ('HR & Payroll',         False, True,  True),
        ('Advanced Reports',     False, True,  True),
        ('M-Pesa Integration',   False, True,  True),
        ('SMS Notifications',    False, True,  True),
        ('Email Notifications',  False, True,  True),
        ('Multi-Branch',         False, False, True),
        ('Priority Support',     False, False, True),
        ('API Access',           False, False, True),
        ('Max Users',            '2',   '10',  '∞'),
    ]
    return render(request, 'billing/choose_plan.html', {
        'prices':     PLAN_PRICES,
        'comparison': comparison,
    })


@login_required
def superadmin_dashboard(request):
    if not request.user.is_superuser and not request.user.is_admin:
        return redirect('dashboard')

    # ✅ FIXED - use timezone.now() instead of date.today()
    now       = timezone.now()
    companies = Company.objects.all().prefetch_related('subscription_payments')
    payments  = SubscriptionPayment.objects.select_related('company').order_by('-created_at')

    total_revenue = sum(p.amount for p in payments if p.status == 'paid')
    expiring_soon = [c for c in companies if c.plan_expires and 0 <= (c.plan_expires - now).days <= 7]
    expired       = [c for c in companies if c.plan_expires and c.plan_expires < now]

    return render(request, 'billing/superadmin.html', {
        'companies':       companies,
        'recent_payments': payments[:20],
        'total_revenue':   total_revenue,
        'total_companies': companies.count(),
        'expiring_soon':   expiring_soon,
        'expired':         expired,
        'today':           now,
    })