from django.contrib import admin

from .models import Pin, PinPurchaseSettings, PinRequest

admin.site.register(Pin)
admin.site.register(PinRequest)
admin.site.register(PinPurchaseSettings)
