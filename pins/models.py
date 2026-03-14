from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string

User = settings.AUTH_USER_MODEL


class Pin(models.Model):
    owner = models.ForeignKey(User, related_name="pins", on_delete=models.CASCADE)
    source_request = models.ForeignKey(
        "PinRequest",
        related_name="generated_pins",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    code = models.CharField(max_length=32, unique=True, blank=True)
    amount = models.PositiveIntegerField(default=1000)
    status = models.CharField(max_length=16, choices=(("unused", "Unused"), ("used", "Used")), default="unused")
    used_by = models.ForeignKey(User, related_name="consumed_pins", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.code:
            # Legacy databases still keep this column at varchar(16), so keep generated codes within that limit.
            self.code = f"NX-{get_random_string(4).upper()}-{get_random_string(4).upper()}-{get_random_string(3).upper()}"
        super().save(*args, **kwargs)


class PinRequest(models.Model):
    user = models.ForeignKey(User, related_name="pin_requests", on_delete=models.CASCADE)
    account_number = models.CharField(max_length=64)
    trx_id = models.CharField(max_length=128)
    quantity = models.PositiveIntegerField(default=1)
    amount = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    admin_note = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=16,
        choices=(("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")),
        default="pending",
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
