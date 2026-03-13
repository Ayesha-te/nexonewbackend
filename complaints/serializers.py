from rest_framework import serializers

from .models import ComplaintFeedback


class ComplaintFeedbackSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    submittedAt = serializers.DateTimeField(source="submitted_at", format="%Y-%m-%d")

    class Meta:
        model = ComplaintFeedback
        fields = ["id", "name", "email", "message", "type", "submittedAt", "status"]

    def get_name(self, obj):
        return obj.user.full_name

    def get_email(self, obj):
        return obj.user.email
