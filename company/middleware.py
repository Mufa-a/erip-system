from django.shortcuts import redirect
from company.models import Company, CompanyUser


class CompanyMiddleware:
    """
    Attaches request.company based on session or membership.
    Handles subscription check safely.
    """

    EXEMPT_URLS = (
        '/accounts/login/',
        '/accounts/logout/',
        '/accounts/register/',
        '/billing/',
        '/admin/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        request.company = None  # always safe default

        if request.user.is_authenticated:

            company_id = request.session.get('company_id')

            # STEP 1: Try session company
            if company_id:
                request.company = Company.objects.filter(
                    pk=company_id,
                    is_active=True
                ).first()

            # STEP 2: fallback to membership
            if not request.company:
                membership = CompanyUser.objects.filter(
                    user=request.user,
                    is_active=True
                ).select_related('company').first()

                if membership:
                    request.company = membership.company
                    request.session['company_id'] = membership.company.id

            # STEP 3: subscription check (ONLY if company exists)
            if request.company:

                is_exempt = any(
                    request.path.startswith(url)
                    for url in self.EXEMPT_URLS
                )

                if (
                    not is_exempt
                    and hasattr(request.company, 'is_subscription_active')
                    and not request.company.is_subscription_active
                ):
                    return redirect('/billing/plans/?expired=1')

        return self.get_response(request)