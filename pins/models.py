from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string

User = settings.AUTH_USER_MODEL

PIN_PRICE = 1000
MIN_PIN_PURCHASE_QUANTITY = 1
MAX_PIN_PURCHASE_QUANTITY = 1000
PIN_PURCHASE_DISABLED_MESSAGE = "PIN/Token Purchase is temporarily unavailable. Please try again later."
SUPPORTED_PIN_PAYMENT_METHODS = ("JazzCash", "Easypaisa", "Bank Account")


def default_pin_payment_methods():
    return [
        {
            "paymentMethod": method,
            "accountTitle": "Sardar Laeiq Ahmed" if method == "Easypaisa" else "",
            "accountNumber": "03448252109" if method == "Easypaisa" else "",
            "bankName": "",
            "instructions": "",
            "qrCodeUrl": None,
            "active": method == "Easypaisa",
        }
        for method in SUPPORTED_PIN_PAYMENT_METHODS
    ]


class PinPurchaseSettings(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ("JazzCash", "JazzCash"),
        ("Easypaisa", "Easypaisa"),
        ("Bank Account", "Bank Account"),
    )

    purchase_enabled = models.BooleanField(default=True)
    available_again_time = models.CharField(max_length=32, blank=True, default="")
    account_title = models.CharField(max_length=128, default="Sardar Laeiq Ahmed")
    account_number = models.CharField(max_length=64, default="03448252109")
    payment_method = models.CharField(max_length=32, choices=PAYMENT_METHOD_CHOICES, default="Easypaisa")
    instructions = models.TextField(
        default="Send payment to this Easypaisa account and submit your transaction ID or proof screenshot for admin approval."
    )
    qr_code = models.FileField(upload_to="pin-payment-qr/", null=True, blank=True)
    payment_methods = models.JSONField(default=default_pin_payment_methods, blank=True)
    # Central, single source of truth for the Joining Fee / PIN Token price - the old
    # module-level PIN_PRICE constant is now only a fallback default for this field.
    standard_price = models.PositiveIntegerField(default=PIN_PRICE)
    promo_enabled = models.BooleanField(default=False)
    promo_price = models.PositiveIntegerField(null=True, blank=True)
    promo_start_at = models.DateTimeField(null=True, blank=True)
    promo_end_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def current(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def is_promo_active(self, *, now=None):
        if not self.promo_enabled or not self.promo_price:
            return False
        now = now or timezone.now()
        if self.promo_start_at and now < self.promo_start_at:
            return False
        if self.promo_end_at and now > self.promo_end_at:
            return False
        return True

    def current_price(self, *, now=None):
        return self.promo_price if self.is_promo_active(now=now) else self.standard_price


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
    account_number = models.CharField(max_length=64, blank=True, default="")
    trx_id = models.CharField(max_length=128)
    quantity = models.PositiveIntegerField(default=1)
    amount = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    payment_screenshot = models.FileField(upload_to="pin-payment-screenshots/", null=True, blank=True)
    admin_note = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=16,
        choices=(("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")),
        default="pending",
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
