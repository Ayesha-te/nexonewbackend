from django.utils.deprecation import MiddlewareMixin

from .automation import run_automation_if_needed


class DailyAutomationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith("/api/"):
            run_automation_if_needed()
