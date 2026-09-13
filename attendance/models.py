from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Attendance(models.Model):
    user = models.ForeignKey(User, related_name="attendance_records", on_delete=models.CASCADE)
    date = models.DateField()
    marked_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "date")
        ordering = ["-date"]
