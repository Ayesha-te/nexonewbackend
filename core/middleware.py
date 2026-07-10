from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from .automation import run_automation_if_needed


class DailyAutomationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not settings.RUN_AUTOMATION_ON_REQUEST:
            return
        if request.method in {"OPTIONS", "HEAD"}:
            return
        if request.path.startswith("/api/auth/"):
            return
        if request.path.startswith("/api/"):
            run_automation_if_needed()
