from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from ads.services import get_users_ads_earning_totals

from .models import Withdrawal
from .serializers import WithdrawalSerializer
from .services import approve_withdrawal, sync_all_pending_withdrawals, sync_user_pending_withdrawal


class MyWithdrawalsView(APIView):
    def get(self, request):
        sync_user_pending_withdrawal(request.user)
        rows = request.user.withdrawals.all().order_by("-date", "-id")
        ads_totals = get_users_ads_earning_totals([request.user.id])
        return Response(WithdrawalSerializer(rows, many=True, context={"ads_totals_by_user_id": ads_totals}).data)


class AdminWithdrawalsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        sync_all_pending_withdrawals()
        rows = list(Withdrawal.objects.all().order_by("-date", "-id"))
        # One aggregate query for every user in the list, not one query per withdrawal row.
        ads_totals = get_users_ads_earning_totals({row.user_id for row in rows})
        return Response(WithdrawalSerializer(rows, many=True, context={"ads_totals_by_user_id": ads_totals}).data)


class AdminApproveWithdrawalView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        withdrawal = Withdrawal.objects.get(pk=pk)
        raw_adjustment = request.data.get("adminAdjustment", 0)
        raw_note = request.data.get("adminNote", "")
        try:
            admin_adjustment = int(raw_adjustment or 0)
        except (TypeError, ValueError):
            return Response({"detail": "Admin adjustment must be a valid whole number."}, status=400)

        try:
            withdrawal = approve_withdrawal(
                withdrawal,
                admin_adjustment=admin_adjustment,
                admin_note=str(raw_note or "").strip(),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(WithdrawalSerializer(withdrawal).data)
