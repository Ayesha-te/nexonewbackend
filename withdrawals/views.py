from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Withdrawal
from .serializers import WithdrawalSerializer


class MyWithdrawalsView(APIView):
    def get(self, request):
        rows = request.user.withdrawals.all().order_by("-date", "-id")
        return Response(WithdrawalSerializer(rows, many=True).data)


class AdminWithdrawalsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        rows = Withdrawal.objects.all().order_by("-date", "-id")
        return Response(WithdrawalSerializer(rows, many=True).data)
