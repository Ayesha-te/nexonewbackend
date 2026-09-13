from django.urls import path

from .views import (
    AdminBroadcastView,
    AdminNotificationLogView,
    AdminNotificationTypesView,
    MarkAllNotificationsReadView,
    MarkNotificationReadView,
    MyNotificationsView,
)

urlpatterns = [
    path("me/", MyNotificationsView.as_view()),
    path("me/<int:pk>/read/", MarkNotificationReadView.as_view()),
    path("me/read-all/", MarkAllNotificationsReadView.as_view()),
    path("admin/types/", AdminNotificationTypesView.as_view()),
    path("admin/broadcast/", AdminBroadcastView.as_view()),
    path("admin/log/", AdminNotificationLogView.as_view()),
]
