from django.contrib import admin

from .models import Notification, NotificationTypeConfig

admin.site.register(Notification)
admin.site.register(NotificationTypeConfig)
