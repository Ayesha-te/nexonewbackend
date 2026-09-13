from django.contrib import admin

from .models import AdsCycle, AdsSettings, AdWatch

admin.site.register(AdsSettings)
admin.site.register(AdsCycle)
admin.site.register(AdWatch)
