import logging
from django.shortcuts import render

logger = logging.getLogger('erp')


def handler404(request, exception):
    logger.warning(f'404: {request.path} — {request.user}')
    return render(request, 'errors/404.html', status=404)


def handler500(request):
    logger.error(f'500: {request.path} — {request.user}')
    return render(request, 'errors/500.html', status=500)


def handler403(request, exception):
    logger.warning(f'403: {request.path} — {request.user}')
    return render(request, 'errors/403.html', status=403)