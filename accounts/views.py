from django.contrib.auth import get_user_model
from rest_framework import permissions
from rest_framework.exceptions import NotFound
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.automation import get_automation_status
from network.services import build_tree_payload

from .models import PinActivationRequest
from .serializers import (
    AdminUserListSerializer,
    AdminUserUpdateSerializer,
    ChangePasswordSerializer,
    PinActivationSerializer,
    ProfileUpdateSerializer,
    SignupLeadSerializer,
    UserSerializer,
)
from .services import create_user_from_pin
from .services import delete_user_subtree

User = get_user_model()


class SignupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignupLeadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lead = serializer.save()
        return Response({"detail": "Signup request submitted.", "lead_id": lead.id}, status=201)


class MeView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        return Response(UserSerializer(request.user, context={"request": request}).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user, context={"request": request}).data)


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data["currentPassword"]):
            return Response({"detail": "Current password is incorrect."}, status=400)
        request.user.set_password(serializer.validated_data["newPassword"])
        request.user.save()
        return Response({"detail": "Password updated."})


class ActivateUserView(APIView):
    def post(self, request):
        serializer = PinActivationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            user = create_user_from_pin(
                activating_user=request.user,
                sponsor_email=request.user.email,
                pin_code=data["pinToken"],
                first_name=data["firstName"],
                last_name=data["lastName"],
                email=data["email"],
                phone=data["phone"],
                account_number=data["accountNumber"],
                position=data["position"],
                payment_method=data["paymentMethod"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        PinActivationRequest.objects.create(
            user=request.user,
            pin_code=data["pinToken"],
            first_name=data["firstName"],
            last_name=data["lastName"],
            email=data["email"],
            phone=data["phone"],
            account_number=data["accountNumber"],
            referral_email=data["referralEmail"],
            position=data["position"],
            payment_method=data["paymentMethod"],
            status="completed",
        )
        return Response(
            {
                "detail": "Account activated.",
                "user_id": user.id,
                "login_email": user.email,
                "login_password": user.email,
            },
            status=201,
        )


class MyTreeView(APIView):
    def get(self, request):
        return Response(build_tree_payload(request.user))


class AdminDashboardView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        users = User.objects.filter(is_staff=False)
        return Response(
            {
                "totalUsers": users.count(),
                "activeUsers": users.filter(is_active=True).count(),
                "totalCurrentIncome": sum(x.current_income for x in users),
                "totalRewardIncome": sum(x.reward_income for x in users),
                "pendingPinRequests": sum(u.pin_requests.filter(status="pending").count() for u in users),
            }
        )


class AdminUsersView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        users = User.objects.filter(is_staff=False).order_by("-created_at")
        return Response(AdminUserListSerializer(users, many=True, context={"request": request}).data)


class AdminSystemStatusView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        status = get_automation_status()
        return Response(
            {
                "today": status["today"],
                "lastAutomationRun": status["last_run_date"],
                "ranToday": status["ran_today"],
                "pendingBackfillDays": status["pending_backfill_days"],
            }
        )


class AdminUserDetailView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, pk):
        user = User.objects.filter(pk=pk, is_staff=False).first()
        if not user:
            raise NotFound("User not found.")
        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AdminUserListSerializer(user, context={"request": request}).data)

    def delete(self, request, pk):
        user = User.objects.filter(pk=pk, is_staff=False).first()
        if not user:
            raise NotFound("User not found.")
        deleted_count = delete_user_subtree(user=user)
        return Response(
            {
                "detail": "User deleted successfully.",
                "deletedCount": deleted_count,
            }
        )
