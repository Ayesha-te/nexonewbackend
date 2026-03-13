from django.contrib import admin

from .models import AutoWithdrawalLog, Withdrawal

admin.site.register(Withdrawal)
admin.site.register(AutoWithdrawalLog)
