from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from .models import Pin, PinRequest
from .serializers import PinRequestCreateSerializer, PinRequestSerializer, PinSerializer


class MyPinsView(APIView):
    def get(self, request):
        available_pins = request.user.pins.filter(status="unused").order_by("-created_at")
        return Response(PinSerializer(available_pins, many=True).data)


class PinRequestView(APIView):
    def get(self, request):
        return Response(PinRequestSerializer(request.user.pin_requests.all().order_by("-created_at"), many=True).data)

    def post(self, request):
        serializer = PinRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = dict(serializer.validated_data)
        validated_data.pop("amount", None)
        pin_request = PinRequest.objects.create(
            user=request.user,
            amount=serializer.validated_data["quantity"] * 1000,
            admin_note="",
            **validated_data,
        )
        return Response(PinRequestSerializer(pin_request).data, status=201)


class AdminPinRequestView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return Response(PinRequestSerializer(PinRequest.objects.all().order_by("-created_at"), many=True).data)

    def post(self, request, pk):
        pin_request = get_object_or_404(PinRequest, pk=pk)
        action = request.data.get("action")
        if pin_request.status != "pending":
            return Response({"detail": f"Request is already {pin_request.status}."}, status=400)
        if action == "approved":
            pin_request.status = "approved"
            pin_request.processed_at = timezone.now()
            pin_request.admin_note = request.data.get("admin_note", "") or ""
            for _ in range(pin_request.quantity):
                Pin.objects.create(owner=pin_request.user, source_request=pin_request, amount=1000)
        elif action == "rejected":
            pin_request.status = "rejected"
            pin_request.processed_at = timezone.now()
            pin_request.admin_note = request.data.get("admin_note", "") or ""
        else:
            return Response({"detail": "Unsupported action."}, status=400)
        pin_request.save()
        return Response(PinRequestSerializer(pin_request).data)
