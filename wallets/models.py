from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Wallet(models.Model):
    user = models.OneToOneField(User, related_name="wallet", on_delete=models.CASCADE)
    balance = models.IntegerField(default=0)
    reward_balance = models.IntegerField(default=0)


class LedgerEntry(models.Model):
    wallet = models.ForeignKey(Wallet, related_name="entries", on_delete=models.CASCADE)
    amount = models.IntegerField()
    entry_type = models.CharField(max_length=32)
    description = models.CharField(max_length=255, blank=True)
    taxable_type = models.CharField(
        max_length=16,
        choices=(("normal", "Normal"), ("cap", "Cap"), ("reward", "Reward")),
        default="normal",
    )
    created_at = models.DateTimeField(default=timezone.now)
