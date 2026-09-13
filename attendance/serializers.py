from rest_framework import serializers

from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="user_id", read_only=True)
    markedAt = serializers.DateTimeField(source="marked_at")

    class Meta:
        model = Attendance
        fields = ["id", "userId", "date", "markedAt"]
