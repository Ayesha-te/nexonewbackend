from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string


class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=32, blank=True)
    account_number = models.CharField(max_length=64, blank=True)
    payment_method = models.CharField(
        max_length=20,
        choices=(("easypaisa", "EasyPaisa"), ("jazzcash", "JazzCash")),
        default="easypaisa",
    )
    referral_code = models.CharField(max_length=12, unique=True, blank=True)
    referred_by = models.ForeignKey(
        "self", related_name="referrals", on_delete=models.SET_NULL, null=True, blank=True
    )
    placement_parent = models.ForeignKey(
        "self", related_name="placements", on_delete=models.SET_NULL, null=True, blank=True
    )
    placement_side = models.CharField(
        max_length=5, choices=(("left", "Left"), ("right", "Right")), blank=True
    )
    left_team_count = models.PositiveIntegerField(default=0)
    right_team_count = models.PositiveIntegerField(default=0)
    pair_count = models.PositiveIntegerField(default=0)
    current_income = models.PositiveIntegerField(default=0)
    reward_income = models.PositiveIntegerField(default=0)
    total_withdrawn = models.PositiveIntegerField(default=0)
    stop_earnings = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to="profiles/", null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    def generate_referral_code(self):
        while True:
            code = f"NX{get_random_string(8).upper()}"
            if not User.objects.filter(referral_code=code).exists():
                return code

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username


class PinActivationRequest(models.Model):
    user = models.ForeignKey(User, related_name="activation_requests", on_delete=models.CASCADE)
    pin_code = models.CharField(max_length=32)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=32)
    account_number = models.CharField(max_length=64)
    referral_email = models.EmailField()
    position = models.CharField(max_length=5, choices=(("left", "Left"), ("right", "Right")))
    payment_method = models.CharField(
        max_length=20,
        choices=(("easypaisa", "EasyPaisa"), ("jazzcash", "JazzCash")),
    )
    status = models.CharField(
        max_length=16,
        choices=(("completed", "Completed"), ("failed", "Failed")),
        default="completed",
    )
    created_at = models.DateTimeField(default=timezone.now)


class SignupLead(models.Model):
    username = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    account_number = models.CharField(max_length=64)
    referral_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
