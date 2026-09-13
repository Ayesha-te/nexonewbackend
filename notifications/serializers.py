from rest_framework import serializers

from .models import Notification, NotificationTypeConfig


class NotificationSerializer(serializers.ModelSerializer):
    notifType = serializers.CharField(source="notif_type")
    isRead = serializers.BooleanField(source="is_read")
    createdAt = serializers.DateTimeField(source="created_at")

    class Meta:
        model = Notification
        fields = ["id", "notifType", "title", "message", "isRead", "createdAt"]


class NotificationTypeConfigSerializer(serializers.ModelSerializer):
    notifType = serializers.CharField(source="notif_type")
    titleTemplate = serializers.CharField(source="title_template")
    messageTemplate = serializers.CharField(source="message_template")

    class Meta:
        model = NotificationTypeConfig
        fields = ["id", "notifType", "enabled", "titleTemplate", "messageTemplate"]
