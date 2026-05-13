from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.health import health_check
from core.error_handlers import handler404, handler500, handler403
from core.views import landing_page, privacy, terms, support, contact, demo

urlpatterns = [
    path('admin/',      admin.site.urls),
    path('',            landing_page,   name='home'),

    # Accounts
    path('accounts/',   include('accounts.urls')),

    # Static pages
    path('privacy/',    privacy,        name='privacy'),
    path('terms/',      terms,          name='terms'),
    path('support/',    support,        name='support'),
    path('contact/',    contact,        name='contact'),
    path('demo/',       demo,           name='demo'),

    # ERP modules
    path('dashboard/',  include('reports.urls')),
    path('customers/',  include('customers.urls')),
    path('products/',   include('products.urls')),
    path('sales/',      include('sales.urls')),
    path('payments/',   include('payments.urls')),
    path('suppliers/',  include('suppliers.urls')),
    path('inventory/',  include('inventory.urls')),
    path('hr/',         include('hr.urls')),
    path('company/',    include('company.urls')),
    path('billing/',    include('billing.urls')),
    path('health/',     health_check,   name='health_check'),
     path('', include('verification.urls', namespace='verification')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = handler404
handler500 = handler500
handler403 = handler403