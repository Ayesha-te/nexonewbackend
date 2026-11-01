from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class RewardTier(models.Model):
    left_target = models.PositiveIntegerField()
    right_target = models.PositiveIntegerField()
    reward = models.CharField(max_length=128)
    amount = models.PositiveIntegerField(default=0)
    sequence = models.PositiveIntegerField(unique=True, db_index=True)


class UserReward(models.Model):
    user = models.ForeignKey(User, related_name="rewards", on_delete=models.CASCADE)
    tier = models.ForeignKey(RewardTier, on_delete=models.CASCADE)
    rewarded_at = models.DateTimeField(default=timezone.now)
    # Frozen at the moment this reward was credited, so a later admin change to
    # RewardTier.amount never retroactively changes what this historical record shows -
    # it always reflects what the user was actually paid.
    amount = models.PositiveIntegerField(default=0)
    ledger_entry = models.ForeignKey(
        "wallets.LedgerEntry", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        unique_together = ("user", "tier")


class SalaryLog(models.Model):
    user = models.ForeignKey(User, related_name="salary_logs", on_delete=models.CASCADE)
    month = models.CharField(max_length=7)
    amount = models.PositiveIntegerField(default=50000)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "month")
