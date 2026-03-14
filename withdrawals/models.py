from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Withdrawal(models.Model):
    user = models.ForeignKey(User, related_name="withdrawals", on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=128, blank=True, default="")
    account_name = models.CharField(max_length=128, blank=True, default="")
    account_number = models.CharField(max_length=64)
    tx_id = models.CharField(max_length=128, blank=True, default="")
    amount = models.PositiveIntegerField()
    tax = models.PositiveIntegerField(default=0)
    tax_type = models.CharField(
        max_length=16,
        choices=(("normal", "Normal"), ("cap", "Cap"), ("reward", "Reward")),
        default="normal",
    )
    net_amount = models.PositiveIntegerField(default=0)
    date = models.DateField(default=timezone.now)
    status = models.CharField(
        max_length=16,
        choices=(("pending", "Pending"), ("processed", "Processed")),
        default="pending",
    )
    auto_generated = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)


class AutoWithdrawalLog(models.Model):
    run_date = models.DateField(unique=True)
    created_at = models.DateTimeField(default=timezone.now)
