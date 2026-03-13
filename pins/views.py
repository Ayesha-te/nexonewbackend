from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Pin, PinRequest
from .serializers import PinRequestCreateSerializer, PinRequestSerializer, PinSerializer


class MyPinsView(APIView):
    def get(self, request):
        return Response(PinSerializer(request.user.pins.all().order_by("-created_at"), many=True).data)


class PinRequestView(APIView):
    def get(self, request):
        return Response(PinRequestSerializer(request.user.pin_requests.all().order_by("-created_at"), many=True).data)

    def post(self, request):
        serializer = PinRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pin_request = PinRequest.objects.create(
            user=request.user,
            amount=serializer.validated_data["quantity"] * 1000,
            **serializer.validated_data,
        )
        return Response(PinRequestSerializer(pin_request).data, status=201)


class AdminPinRequestView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return Response(PinRequestSerializer(PinRequest.objects.all().order_by("-created_at"), many=True).data)

    def post(self, request, pk):
        pin_request = PinRequest.objects.get(pk=pk)
        action = request.data.get("action")
        if action == "approved":
            pin_request.status = "approved"
            for _ in range(pin_request.quantity):
                Pin.objects.create(owner=pin_request.user, amount=1000)
        elif action == "rejected":
            pin_request.status = "rejected"
        pin_request.save()
        return Response(PinRequestSerializer(pin_request).data)
