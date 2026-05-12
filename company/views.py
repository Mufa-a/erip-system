# company/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Company, CompanyUser, MpesaSettings
from accounts.models import User
import logging

logger = logging.getLogger(__name__)


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
        CompanyUser.objects.create(
            company = company,
            user    = request.user,
            role    = CompanyUser.Role.OWNER
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

    # ── Pass M-Pesa status for the badge in the template ──
    mpesa_configured = False
    mpesa_active     = False
    try:
        mpesa = company.mpesa_settings
        mpesa_configured = mpesa.is_configured
        mpesa_active     = mpesa.is_active and mpesa.is_configured
    except Exception:
        pass  # No row yet — badge shows "Not Configured"

    return render(request, 'company/company_settings.html', {
        'company':          company,
        'mpesa_configured': mpesa_configured,
        'mpesa_active':     mpesa_active,
        'all_users': User.objects.exclude(
            companies__company=company
        ).order_by('username'),
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
                company  = request.company,
                user     = user,
                defaults = {'role': role}
            )
            messages.success(request, f'{username} added to company!')
        except User.DoesNotExist:
            messages.error(request, f'User {username} not found.')
        return redirect('company_settings')

    return redirect('company_settings')


# ============================================================
# M-Pesa Settings — per company
# ============================================================

@login_required
def mpesa_settings(request):
    if not request.company:
        return redirect('company_create')

    mpesa_cfg, created = MpesaSettings.objects.get_or_create(
        company=request.company
    )

    if request.method == 'POST':
        environment     = request.POST.get('environment', 'sandbox')
        shortcode       = request.POST.get('shortcode', '').strip()
        callback_url    = request.POST.get('callback_url', '').strip()
        consumer_key    = request.POST.get('consumer_key', '').strip()
        consumer_secret = request.POST.get('consumer_secret', '').strip()
        passkey         = request.POST.get('passkey', '').strip()

        mpesa_cfg.environment  = environment
        mpesa_cfg.callback_url = callback_url

        # Only overwrite encrypted fields if user typed a new value
        if shortcode:
            mpesa_cfg.shortcode = shortcode
        if consumer_key:
            mpesa_cfg.consumer_key = consumer_key
        if consumer_secret:
            mpesa_cfg.consumer_secret = consumer_secret
        if passkey:
            mpesa_cfg.passkey = passkey

        mpesa_cfg.save()
        messages.success(request, 'M-Pesa settings saved successfully!')
        return redirect('mpesa_settings')

    return render(request, 'company/mpesa_settings.html', {
        'mpesa_cfg':           mpesa_cfg,
        'company':             request.company,
        'has_consumer_key':    bool(mpesa_cfg._consumer_key),
        'has_consumer_secret': bool(mpesa_cfg._consumer_secret),
        'has_passkey':         bool(mpesa_cfg._passkey),
        'shortcode_display':   mpesa_cfg.shortcode or '',
    })


@login_required
def mpesa_test(request):
    """AJAX — tests credentials by fetching a Safaricom token."""
    if not request.company:
        return JsonResponse({'success': False, 'message': 'No company selected.'})

    try:
        mpesa_cfg = MpesaSettings.objects.filter(
            company=request.company
        ).first()

        if not mpesa_cfg or not mpesa_cfg.is_configured:
            return JsonResponse({
                'success': False,
                'message': 'Please fill in all M-Pesa fields first.'
            })

        from core.mpesa import get_mpesa_token

        # ✅ 'environment' matches the parameter name in core/mpesa.py
        token = get_mpesa_token(
            consumer_key    = mpesa_cfg.consumer_key,
            consumer_secret = mpesa_cfg.consumer_secret,
            environment     = mpesa_cfg.environment,
        )

        if token:
            mpesa_cfg.is_active = True
            mpesa_cfg.save()
            return JsonResponse({
                'success': True,
                'message': f'✓ Connected! ({mpesa_cfg.get_environment_display()}) Credentials are valid.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Could not get token. Check your Consumer Key and Secret.'
            })

    except Exception as e:
        logger.error(f"M-Pesa test failed for {request.company}: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Connection failed: {str(e)}'
        })