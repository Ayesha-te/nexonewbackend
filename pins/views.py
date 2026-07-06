import json

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from .models import PIN_PRICE, PIN_PURCHASE_DISABLED_MESSAGE, Pin, PinPurchaseSettings, PinRequest
from .serializers import (
    PinPurchaseSettingsSerializer,
    PinRequestCreateSerializer,
    PinRequestSerializer,
    PinSerializer,
)

User = get_user_model()


def has_active_pin_payment_method(settings):
    return any(bool(method.get("active")) for method in (settings.payment_methods or []))


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
        if not has_active_pin_payment_method(settings):
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


class AdminPinBalancesView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        users = (
            User.objects.filter(pins__isnull=False, is_staff=False)
            .annotate(
                total_pins=Count("pins", distinct=True),
                available_pins=Count("pins", filter=Q(pins__status="unused"), distinct=True),
                used_pins=Count("pins", filter=Q(pins__status="used"), distinct=True),
            )
            .filter(total_pins__gt=0)
            .order_by("-available_pins", "-total_pins", "email")
        )

        rows = []
        for user in users:
            rows.append(
                {
                    "userId": user.id,
                    "userName": user.full_name,
                    "email": user.email,
                    "phone": user.phone,
                    "accountNumber": user.account_number,
                    "paymentMethod": user.payment_method,
                    "bankName": user.bank_name,
                    "totalPins": user.total_pins,
                    "availablePins": user.available_pins,
                    "usedPins": user.used_pins,
                }
            )
        return Response(rows)


class AdminPinSettingsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return Response(PinPurchaseSettingsSerializer(PinPurchaseSettings.current(), context={"request": request}).data)

    def post(self, request):
        settings = PinPurchaseSettings.current()
        settings.available_again_time = str(request.data.get("availableAgainTime", "")).strip()

        raw_methods = request.data.get("paymentMethods")
        if raw_methods:
            try:
                payment_methods = json.loads(raw_methods)
            except json.JSONDecodeError:
                return Response({"detail": "Invalid payment methods data."}, status=400)
        else:
            payment_methods = [
                {
                    "paymentMethod": request.data.get("paymentMethod", settings.payment_method),
                    "accountTitle": request.data.get("accountTitle", settings.account_title),
                    "accountNumber": request.data.get("accountNumber", settings.account_number),
                    "bankName": request.data.get("bankName", ""),
                    "instructions": request.data.get("instructions", settings.instructions),
                    "qrCodeUrl": settings.qr_code.url if settings.qr_code else None,
                }
            ]

        cleaned_methods = []
        active_method_seen = False
        for index, method in enumerate(payment_methods):
            payment_method = str(method.get("paymentMethod", "")).strip()
            account_title = str(method.get("accountTitle", "")).strip()
            account_number = str(method.get("accountNumber", "")).strip()
            bank_name = str(method.get("bankName", "")).strip()
            instructions = str(method.get("instructions", "")).strip()
            qr_code_url = method.get("qrCodeUrl") or None
            is_active = bool(method.get("active")) and not active_method_seen
            if is_active:
                active_method_seen = True

            upload = request.FILES.get(f"qrCode_{index}")
            if upload:
                saved_path = default_storage.save(f"pin-payment-qr/{upload.name}", upload)
                qr_code_url = default_storage.url(saved_path)

            if not payment_method:
                return Response({"detail": "Each payment method needs a method name."}, status=400)
            if is_active and (not account_title or not account_number):
                return Response({"detail": "The active payment method needs account title and account number."}, status=400)
            if is_active and payment_method == "Bank Account" and not bank_name:
                return Response({"detail": "The active bank account payment method needs a bank name."}, status=400)

            cleaned_methods.append(
                {
                    "paymentMethod": payment_method,
                    "accountTitle": account_title,
                    "accountNumber": account_number,
                    "bankName": bank_name,
                    "instructions": instructions,
                    "qrCodeUrl": qr_code_url,
                    "active": is_active,
                }
            )

        if not cleaned_methods:
            return Response({"detail": "At least one payment method is required."}, status=400)

        first_method = cleaned_methods[0]
        settings.payment_method = first_method["paymentMethod"]
        settings.account_title = first_method["accountTitle"]
        settings.account_number = first_method["accountNumber"]
        settings.instructions = first_method["instructions"]
        settings.payment_methods = cleaned_methods
        settings.purchase_enabled = any(method["active"] for method in cleaned_methods)
        settings.save()
        return Response(PinPurchaseSettingsSerializer(settings, context={"request": request}).data)
