from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('reports.urls')),
    path('customers/', include('customers.urls')),
    path('products/', include('products.urls')),
    path('sales/', include('sales.urls')),
    path('payments/', include('payments.urls')),
    path('suppliers/', include('suppliers.urls')),
    path('inventory/', include('inventory.urls')),
    path('hr/', include('hr.urls')),
    path('company/', include('company.urls')),
    path('', include('accounts.urls')),
    path('billing/', include('billing.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)