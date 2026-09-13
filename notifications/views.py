from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, NotificationTypeConfig
from .serializers import NotificationSerializer, NotificationTypeConfigSerializer
from .services import broadcast


class MyNotificationsView(APIView):
    def get(self, request):
        rows = request.user.notifications.all().order_by("-created_at")[:50]
        unread_count = request.user.notifications.filter(is_read=False).count()
        return Response(
            {
                "results": NotificationSerializer(rows, many=True).data,
                "unreadCount": unread_count,
            }
        )


class MarkNotificationReadView(APIView):
    def post(self, request, pk):
        try:
            notification = request.user.notifications.get(pk=pk)
        except Notification.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)

        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data)


class MarkAllNotificationsReadView(APIView):
    def post(self, request):
        updated = request.user.notifications.filter(is_read=False).update(is_read=True)
        return Response({"updated": updated})


class AdminNotificationTypesView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        rows = NotificationTypeConfig.objects.all().order_by("notif_type")
        return Response(NotificationTypeConfigSerializer(rows, many=True).data)

    def post(self, request):
        items = request.data if isinstance(request.data, list) else []
        for item in items:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id")
            if item_id is None:
                continue
            config = NotificationTypeConfig.objects.filter(pk=item_id).first()
            if config is None:
                continue

            if "enabled" in item:
                config.enabled = bool(item.get("enabled"))
            if "titleTemplate" in item:
                config.title_template = item.get("titleTemplate") or ""
            if "messageTemplate" in item:
                config.message_template = item.get("messageTemplate") or ""
            config.save()

        rows = NotificationTypeConfig.objects.all().order_by("notif_type")
        return Response(NotificationTypeConfigSerializer(rows, many=True).data)


class AdminBroadcastView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        title = request.data.get("title")
        message = request.data.get("message")
        user_ids = request.data.get("userIds", "all")

        if not isinstance(title, str) or not title.strip():
            return Response({"detail": "Title is required."}, status=400)
        if not isinstance(message, str) or not message.strip():
            return Response({"detail": "Message is required."}, status=400)

        sent = broadcast(title, message, user_ids=user_ids)
        return Response({"sent": sent})


class AdminNotificationLogView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        rows = Notification.objects.select_related("user").order_by("-created_at")
        notif_type = request.query_params.get("notifType")
        if notif_type:
            rows = rows.filter(notif_type=notif_type)
        return Response(NotificationSerializer(rows[:500], many=True).data)
