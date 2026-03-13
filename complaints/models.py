from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class ComplaintFeedback(models.Model):
    user = models.ForeignKey(User, related_name="complaint_feedback", on_delete=models.CASCADE)
    message = models.TextField()
    type = models.CharField(max_length=16, choices=(("feedback", "Feedback"), ("complaint", "Complaint")))
    status = models.CharField(
        max_length=16,
        choices=(("new", "New"), ("reviewed", "Reviewed"), ("resolved", "Resolved")),
        default="new",
    )
    submitted_at = models.DateTimeField(default=timezone.now)
