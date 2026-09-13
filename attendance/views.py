from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import AttendanceSerializer
from .services import (
    get_monthly_ranking,
    get_monthly_summary,
    get_today_attendance_list,
    get_user_history,
    mark_attendance,
)

User = get_user_model()


class MarkAttendanceView(APIView):
    def post(self, request):
        attendance, created = mark_attendance(request.user)
        return Response(
            {
                "date": str(attendance.date),
                "markedAt": attendance.marked_at.isoformat(),
                "alreadyMarked": not created,
            }
        )


class MyAttendanceHistoryView(APIView):
    def get(self, request):
        month = request.query_params.get("month")
        history = get_user_history(request.user, month)
        summary = get_monthly_summary(request.user, month or timezone.localdate().strftime("%Y-%m"))
        return Response(
            {
                "records": AttendanceSerializer(history["records"], many=True).data,
                "totalDays": history["totalDays"],
                "currentStreak": history["currentStreak"],
                "summary": summary,
            }
        )


class AdminTodayAttendanceView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return Response(get_today_attendance_list())


class AdminUserAttendanceView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk, is_staff=False)
        month = request.query_params.get("month")
        history = get_user_history(user, month)
        summary = get_monthly_summary(user, month or timezone.localdate().strftime("%Y-%m"))
        return Response(
            {
                "userId": user.id,
                "userName": user.full_name,
                "email": user.email,
                "phone": user.phone,
                "records": AttendanceSerializer(history["records"], many=True).data,
                "totalDays": history["totalDays"],
                "currentStreak": history["currentStreak"],
                "summary": summary,
            }
        )


class AdminAttendanceRankingView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        month = request.query_params.get("month")
        return Response(get_monthly_ranking(month))
