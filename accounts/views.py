from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import F, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils.crypto import get_random_string
from django.utils import timezone
from rest_framework import permissions
from rest_framework.exceptions import NotFound
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.automation import get_automation_status
from network.services import build_tree_payload
from wallets.models import LedgerEntry
from withdrawals.models import Withdrawal

from .models import PinActivationRequest, SiteSetting
from .serializers import (
    AdminUserListSerializer,
    AdminUserUpdateSerializer,
    ChangePasswordSerializer,
    LeaderboardUserSerializer,
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
                sponsor_email=data["referralEmail"],
                pin_code=data["pinToken"],
                first_name=data["firstName"],
                last_name=data["lastName"],
                email=data["email"],
                phone=data["phone"],
                account_number=data["accountNumber"],
                bank_name=data.get("bankName", ""),
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
            bank_name=data.get("bankName", ""),
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


class LeaderboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        now = timezone.localtime()
        week_start = now - timedelta(days=7)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        leaders = (
            User.objects.filter(is_staff=False, is_active=True)
            .annotate(
                currentIncome=F("current_income"),
                weeklyIncome=Coalesce(
                    Sum(
                        "wallet__entries__amount",
                        filter=Q(wallet__entries__amount__gt=0, wallet__entries__created_at__gte=week_start),
                    ),
                    Value(0),
                    output_field=IntegerField(),
                ),
                monthlyIncome=Coalesce(
                    Sum(
                        "wallet__entries__amount",
                        filter=Q(wallet__entries__amount__gt=0, wallet__entries__created_at__gte=month_start),
                    ),
                    Value(0),
                    output_field=IntegerField(),
                ),
                totalIncome=Coalesce(
                    Sum("wallet__entries__amount", filter=Q(wallet__entries__amount__gt=0)),
                    F("current_income") + F("reward_income"),
                    output_field=IntegerField(),
                ),
            )
            .filter(totalIncome__gte=100)
            .order_by("-totalIncome", "-monthlyIncome", "-weeklyIncome", "id")[:3]
        )
        return Response(LeaderboardUserSerializer(leaders, many=True, context={"request": request}).data)


class IncomeHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        now = timezone.localtime()
        today = now.date()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_end = month_start
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)
        three_month_start = (month_start - timedelta(days=75)).replace(day=1)
        week_start = now - timedelta(days=7)

        entries = LedgerEntry.objects.filter(wallet__user=request.user, amount__gt=0)

        def total_since(start, end=None):
            qs = entries.filter(created_at__gte=start)
            if end is not None:
                qs = qs.filter(created_at__lt=end)
            return qs.aggregate(total=Coalesce(Sum("amount"), Value(0), output_field=IntegerField()))["total"]

        monthly_history = []
        for offset in range(5, -1, -1):
            first_day = (month_start - timedelta(days=offset * 31)).replace(day=1)
            next_month = (first_day + timedelta(days=32)).replace(day=1)
            monthly_history.append(
                {
                    "label": first_day.strftime("%b %Y"),
                    "amount": total_since(first_day, next_month),
                }
            )

        weekly_history = []
        for offset in range(5, -1, -1):
            start_date = today - timedelta(days=(offset + 1) * 7)
            end_date = today - timedelta(days=offset * 7)
            weekly_history.append(
                {
                    "label": f"{start_date.strftime('%d %b')} - {end_date.strftime('%d %b')}",
                    "amount": entries.filter(created_at__date__gte=start_date, created_at__date__lt=end_date)
                    .aggregate(total=Coalesce(Sum("amount"), Value(0), output_field=IntegerField()))["total"],
                }
            )

        total_income = entries.aggregate(total=Coalesce(Sum("amount"), Value(0), output_field=IntegerField()))["total"]
        current_month = total_since(month_start)
        last_month = total_since(last_month_start, last_month_end)
        last_three_months = total_since(three_month_start)
        weekly_income = total_since(week_start)

        return Response(
            {
                "currentIncome": request.user.current_income,
                "currentMonthIncome": current_month,
                "lastMonthIncome": last_month,
                "last3MonthsIncome": last_three_months,
                "weeklyIncome": weekly_income,
                "totalIncome": total_income or (request.user.current_income + request.user.reward_income),
                "monthlyHistory": monthly_history,
                "weeklyHistory": weekly_history,
            }
        )


class DashboardNotificationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        hour = timezone.localtime().hour
        greeting = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 17 else "Good Evening"
        messages = [f"Assalam-o-Alaikum, {greeting}. Keep growing your Nexocart network."]

        latest_entries = (
            LedgerEntry.objects.filter(amount__gt=0)
            .select_related("wallet__user")
            .order_by("-created_at")[:5]
        )
        for entry in latest_entries:
            name = entry.wallet.user.full_name
            messages.append(f"Congratulations {name}, income received: PKR {entry.amount:,}.")

        latest_withdrawals = (
            Withdrawal.objects.filter(status="processed")
            .select_related("user")
            .order_by("-created_at")[:5]
        )
        for withdrawal in latest_withdrawals:
            messages.append(f"Withdrawal Successful: {withdrawal.user.full_name} received PKR {withdrawal.net_amount:,}.")

        if request.user.left_team_count or request.user.right_team_count:
            messages.append(f"Team Growth Update: Left {request.user.left_team_count} / Right {request.user.right_team_count}.")

        if request.user.reward_income > 0:
            messages.append(f"Reward Achieved: You have earned PKR {request.user.reward_income:,} reward income.")

        return Response({"messages": messages[:12]})


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


class AdminPasswordResetView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        email = str(request.data.get("email", "")).strip()
        if not email:
            return Response({"detail": "Email is required."}, status=400)

        user = User.objects.filter(email__iexact=email, is_staff=False).first()
        if not user:
            return Response({"detail": "User not found."}, status=404)

        new_password = f"NX-{get_random_string(4).upper()}-{get_random_string(4).upper()}"
        user.set_password(new_password)
        user.save(update_fields=["password"])

        return Response(
            {
                "detail": "Password reset successfully.",
                "email": user.email,
                "userName": user.full_name,
                "newPassword": new_password,
            }
        )


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


class SiteSettingsView(APIView):
    def get(self, request):
        settings = SiteSetting.current()
        return Response(
            {
                "usdRatePkr": float(settings.usd_rate_pkr),
                "updatedAt": settings.updated_at,
            }
        )


class AdminSiteSettingsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        settings = SiteSetting.current()
        return Response(
            {
                "usdRatePkr": float(settings.usd_rate_pkr),
                "updatedAt": settings.updated_at,
            }
        )

    def post(self, request):
        try:
            usd_rate_pkr = float(request.data.get("usdRatePkr", 0))
        except (TypeError, ValueError):
            return Response({"detail": "USD rate must be a valid number."}, status=400)

        if usd_rate_pkr <= 0:
            return Response({"detail": "USD rate must be greater than 0."}, status=400)

        settings = SiteSetting.current()
        settings.usd_rate_pkr = usd_rate_pkr
        settings.save(update_fields=["usd_rate_pkr", "updated_at"])
        return Response(
            {
                "usdRatePkr": float(settings.usd_rate_pkr),
                "updatedAt": settings.updated_at,
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
