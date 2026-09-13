from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL

NOTIF_TYPE_CHOICES = (
    ("welcome", "Welcome"),
    ("ads_available", "Ads Available"),
    ("ads_reminder", "Ads Reminder"),
    ("pair_completed", "Pair Completed"),
    ("ads_unlocked", "Ads Unlocked"),
    ("ads_cycle_renewed", "Ads Cycle Renewed"),
    ("ads_cycle_ending", "Ads Cycle Ending"),
    ("ads_locked", "Ads Locked"),
    ("daily_ads_completed", "Daily Ads Completed"),
    ("admin_custom", "Admin Custom"),
)


class NotificationTypeConfig(models.Model):
    notif_type = models.CharField(max_length=32, choices=NOTIF_TYPE_CHOICES, unique=True)
    enabled = models.BooleanField(default=True)
    title_template = models.CharField(max_length=255)
    message_template = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.notif_type


class Notification(models.Model):
    user = models.ForeignKey(User, related_name="notifications", on_delete=models.CASCADE)
    notif_type = models.CharField(max_length=32, choices=NOTIF_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.notif_type} -> {self.user_id}"
