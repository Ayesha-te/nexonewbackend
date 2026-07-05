from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from .models import PIN_PRICE, PIN_PURCHASE_DISABLED_MESSAGE, Pin, PinPurchaseSettings, PinRequest
from .serializers import (
    PinPurchaseSettingsSerializer,
    PinPurchaseSettingsUpdateSerializer,
    PinRequestCreateSerializer,
    PinRequestSerializer,
    PinSerializer,
)


class MyPinsView(APIView):
    def get(self, request):
        return Response(PinSerializer(request.user.pins.all().order_by("-created_at"), many=True).data)


class PinRequestView(APIView):
    def get(self, request):
        return Response(
            PinRequestSerializer(
                request.user.pin_requests.all().order_by("-created_at"),
                many=True,
                context={"request": request},
            ).data
        )

    def post(self, request):
        settings = PinPurchaseSettings.current()
        if not settings.purchase_enabled:
            return Response({"detail": PIN_PURCHASE_DISABLED_MESSAGE}, status=403)

        serializer = PinRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = dict(serializer.validated_data)
        proof_file = validated_data.pop("proofFile")
        pin_request = PinRequest.objects.create(
            user=request.user,
            admin_note="",
            payment_screenshot=proof_file,
            **validated_data,
        )
        return Response(PinRequestSerializer(pin_request, context={"request": request}).data, status=201)


class PinConfigView(APIView):
    def get(self, request):
        return Response(PinPurchaseSettingsSerializer(PinPurchaseSettings.current(), context={"request": request}).data)


class AdminPinRequestView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return Response(
            PinRequestSerializer(
                PinRequest.objects.all().order_by("-created_at"),
                many=True,
                context={"request": request},
            ).data
        )

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
                Pin.objects.create(owner=pin_request.user, source_request=pin_request, amount=PIN_PRICE)
        elif action == "rejected":
            pin_request.status = "rejected"
            pin_request.processed_at = timezone.now()
            pin_request.admin_note = request.data.get("admin_note", "") or ""
        else:
            return Response({"detail": "Unsupported action."}, status=400)
        pin_request.save()
        return Response(PinRequestSerializer(pin_request, context={"request": request}).data)


class AdminPinSettingsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return Response(PinPurchaseSettingsSerializer(PinPurchaseSettings.current(), context={"request": request}).data)

    def post(self, request):
        settings = PinPurchaseSettings.current()
        data = request.data.copy()
        if "proofFile" in request.FILES:
            data["qrCode"] = request.FILES["proofFile"]
        serializer = PinPurchaseSettingsUpdateSerializer(settings, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        settings = serializer.save()
        return Response(PinPurchaseSettingsSerializer(settings, context={"request": request}).data)
