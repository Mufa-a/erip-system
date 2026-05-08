from django.shortcuts import redirect
from django.utils import timezone


class CompanyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    EXEMPT_URLS = [
        '/accounts/', '/billing/', '/company/switch/', '/admin/'
    ]

    def __call__(self, request):
        if request.user.is_authenticated:
            company_id = request.session.get('company_id')
            if company_id:
                try:
                    from company.models import Company
                    request.company = Company.objects.get(pk=company_id, is_active=True)
                except Company.DoesNotExist:
                    request.company = None
            else:
                from company.models import CompanyUser
                membership = CompanyUser.objects.filter(
                    user=request.user, is_active=True
                ).select_related('company').first()
                if membership:
                    request.company = membership.company
                    request.session['company_id'] = membership.company.id
                else:
                    request.company = None

            if request.company:
                exempt = any(request.path.startswith(u) for u in self.EXEMPT_URLS)
                if not exempt and not request.company.is_subscription_active:
                    return redirect('/billing/plans/?expired=1')
        else:
            request.company = None

        return self.get_response(request)