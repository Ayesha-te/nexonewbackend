from django.contrib import admin

from .models import AdsCycle, AdsSettings, AdVideo, AdWatch

admin.site.register(AdsSettings)
admin.site.register(AdsCycle)
admin.site.register(AdVideo)
admin.site.register(AdWatch)
