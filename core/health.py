from django.http import JsonResponse
from django.db import connection
from django.utils import timezone


def health_check(request):
    checks = {
        'status': 'ok',
        'timestamp': timezone.now().isoformat(),
        'database': 'ok',
        'version': '1.0.0',
    }

    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        checks['database'] = 'ok'
    except Exception as e:
        checks['database'] = f'error: {str(e)}'
        checks['status']   = 'degraded'

    status_code = 200 if checks['status'] == 'ok' else 503
    return JsonResponse(checks, status=status_code)