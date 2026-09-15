from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


def get_ad_video_storage():
    # Callable (not an instance) so Django migrations serialize this as a stable dotted
    # path instead of baking in a storage instance. Falls back to Django's default
    # (local disk) storage when Cloudinary isn't configured, e.g. local development.
    if getattr(settings, "CLOUDINARY_URL", ""):
        from .storage import VideoCloudinaryStorage

        return VideoCloudinaryStorage()
    from django.core.files.storage import default_storage

    return default_storage


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


class AdVideo(models.Model):
    title = models.CharField(max_length=128, blank=True, default="")
    video = models.FileField(upload_to="ads-videos/", storage=get_ad_video_storage)
    duration_seconds = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)


class AdWatch(models.Model):
    STATUS_CHOICES = (
        ("started", "Started"),
        ("completed", "Completed"),
    )

    user = models.ForeignKey(User, related_name="ad_watches", on_delete=models.CASCADE)
    cycle = models.ForeignKey(AdsCycle, related_name="watches", null=True, blank=True, on_delete=models.SET_NULL)
    video = models.ForeignKey(AdVideo, related_name="watches", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="completed")
    watched_date = models.DateField()
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    reward_pkr = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
