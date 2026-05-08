from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Sum, Count
from company.models import Company, SubscriptionPayment


@staff_member_required
def superadmin_dashboard(request):
    companies    = Company.objects.annotate(member_count=Count('members')).order_by('-created_at')
    total_revenue = SubscriptionPayment.objects.filter(
        status='paid'
    ).aggregate(total=Sum('amount'))['total'] or 0

    expiring_soon = Company.objects.filter(
        plan_expires__lte=timezone.now().date() + timezone.timedelta(days=7),
        plan_expires__gte=timezone.now().date(),
        is_active=True
    )

    expired = Company.objects.filter(
        plan_expires__lt=timezone.now().date(),
        is_active=True
    )

    recent_payments = SubscriptionPayment.objects.filter(
        status='paid'
    ).select_related('company').order_by('-paid_at')[:20]

    return render(request, 'billing/superadmin.html', {
        'companies':      companies,
        'total_revenue':  total_revenue,
        'expiring_soon':  expiring_soon,
        'expired':        expired,
        'recent_payments': recent_payments,
    })