from django.shortcuts import redirect
from .models import ServiceStatus

class ServiceStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if ServiceStatus.objects.exists():
            active = ServiceStatus.objects.first().active  # type: ignore
            admin = request.path.startswith('/admin/') or request.path.startswith('/ticket/admin/')
            if not active:
                if not (admin or request.path == '/ticket/unavailable/'):
                    return redirect('service_unavailable')
                else:
                    pass  # allow admin
            else:
                pass  # servicable
        response = self.get_response(request)
        return response