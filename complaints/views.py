from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ComplaintFeedback
from .serializers import ComplaintFeedbackSerializer


class ComplaintFeedbackView(APIView):
    def get(self, request):
        rows = ComplaintFeedback.objects.filter(user=request.user).order_by("-submitted_at")
        return Response(ComplaintFeedbackSerializer(rows, many=True).data)

    def post(self, request):
        obj = ComplaintFeedback.objects.create(
            user=request.user,
            message=request.data.get("message", ""),
            type=request.data.get("type", "feedback"),
        )
        return Response(ComplaintFeedbackSerializer(obj).data, status=201)


class AdminComplaintFeedbackView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        rows = ComplaintFeedback.objects.all().order_by("-submitted_at")
        return Response(ComplaintFeedbackSerializer(rows, many=True).data)

    def patch(self, request, pk):
        obj = ComplaintFeedback.objects.get(pk=pk)
        obj.status = request.data.get("status", obj.status)
        obj.save()
        return Response(ComplaintFeedbackSerializer(obj).data)
