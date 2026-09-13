from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class AdsSettings(models.Model):
    enabled = models.BooleanField(default=True)
    daily_limit = models.PositiveIntegerField(default=3)
    welcome_reward_pkr = models.PositiveIntegerField(default=11)
    welcome_duration_days = models.PositiveIntegerField(default=3)
    pair_reward_pkr = models.PositiveIntegerField(default=5)
    pair_cycle_days = models.PositiveIntegerField(default=3)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def current(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class AdsCycle(models.Model):
    CYCLE_TYPE_CHOICES = (
        ("welcome", "Welcome"),
        ("pair", "Pair"),
    )
    STATUS_CHOICES = (
        ("active", "Active"),
        ("expired", "Expired"),
    )

    user = models.ForeignKey(User, related_name="ads_cycles", on_delete=models.CASCADE)
    cycle_type = models.CharField(max_length=16, choices=CYCLE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="active")
    ending_notified = models.BooleanField(default=False)
    expired_notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(status="active"),
                name="unique_active_ads_cycle_per_user",
            ),
        ]


class AdWatch(models.Model):
    user = models.ForeignKey(User, related_name="ad_watches", on_delete=models.CASCADE)
    cycle = models.ForeignKey(AdsCycle, related_name="watches", null=True, blank=True, on_delete=models.SET_NULL)
    watched_date = models.DateField()
    reward_pkr = models.PositiveIntegerField()
    created_at = models.DateTimeField(default=timezone.now)
