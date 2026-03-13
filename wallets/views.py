from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LedgerEntrySerializer, WalletSerializer
from .services import ensure_wallet


class MyWalletView(APIView):
    def get(self, request):
        return Response(WalletSerializer(ensure_wallet(request.user)).data)


class MyLedgerView(APIView):
    def get(self, request):
        wallet = ensure_wallet(request.user)
        return Response(LedgerEntrySerializer(wallet.entries.all().order_by("-created_at"), many=True).data)
