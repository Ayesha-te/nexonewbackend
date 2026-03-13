from django.contrib import admin

from .models import RewardTier, SalaryLog, UserReward

admin.site.register(RewardTier)
admin.site.register(UserReward)
admin.site.register(SalaryLog)
