from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import PinActivationRequest, SignupLead, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "username", "is_staff", "is_active", "is_approved", "pair_count")
    search_fields = ("email", "username", "referral_code")
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "MLM",
            {
                "fields": (
                    "phone",
                    "account_number",
                    "payment_method",
                    "referral_code",
                    "referred_by",
                    "placement_parent",
                    "placement_side",
                    "left_team_count",
                    "right_team_count",
                    "pair_count",
                    "current_income",
                    "reward_income",
                    "total_withdrawn",
                    "stop_earnings",
                    "is_approved",
                    "profile_picture",
                )
            },
        ),
    )


admin.site.register(PinActivationRequest)
admin.site.register(SignupLead)
