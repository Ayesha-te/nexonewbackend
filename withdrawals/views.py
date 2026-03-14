from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Withdrawal
from .serializers import WithdrawalSerializer
from .services import approve_withdrawal, sync_all_pending_withdrawals, sync_user_pending_withdrawal


class MyWithdrawalsView(APIView):
    def get(self, request):
        sync_user_pending_withdrawal(request.user)
        rows = request.user.withdrawals.all().order_by("-date", "-id")
        return Response(WithdrawalSerializer(rows, many=True).data)


class AdminWithdrawalsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        sync_all_pending_withdrawals()
        rows = Withdrawal.objects.all().order_by("-date", "-id")
        return Response(WithdrawalSerializer(rows, many=True).data)


class AdminApproveWithdrawalView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        withdrawal = Withdrawal.objects.get(pk=pk)
        try:
            withdrawal = approve_withdrawal(withdrawal)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(WithdrawalSerializer(withdrawal).data)
