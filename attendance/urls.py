from django.urls import path

from .views import (
    AdminAttendanceRankingView,
    AdminTodayAttendanceView,
    AdminUserAttendanceView,
    MarkAttendanceView,
    MyAttendanceHistoryView,
)

urlpatterns = [
    path("me/mark/", MarkAttendanceView.as_view()),
    path("me/history/", MyAttendanceHistoryView.as_view()),
    path("admin/today/", AdminTodayAttendanceView.as_view()),
    path("admin/user/<int:pk>/", AdminUserAttendanceView.as_view()),
    path("admin/ranking/", AdminAttendanceRankingView.as_view()),
]
