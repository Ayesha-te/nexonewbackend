from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AdsSettings, AdWatch
from .serializers import AdsSettingsSerializer, AdWatchSerializer
from .services import get_ads_status, watch_ad


class MyAdsStatusView(APIView):
    def get(self, request):
        return Response(get_ads_status(request.user))


class MyAdsWatchView(APIView):
    def post(self, request):
        try:
            watch_ad(request.user)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(get_ads_status(request.user))


class AdminAdsSettingsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return Response(AdsSettingsSerializer(AdsSettings.current()).data)

    def post(self, request):
        settings = AdsSettings.current()
        serializer = AdsSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AdminAdsHistoryView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        rows = AdWatch.objects.select_related("user", "cycle").order_by("-created_at")
        user_id = request.query_params.get("userId")
        if user_id:
            rows = rows.filter(user_id=user_id)
        return Response(AdWatchSerializer(rows[:500], many=True).data)
