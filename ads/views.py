from datetime import date

from rest_framework import permissions
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AdsSettings, AdVideo, AdWatch
from .serializers import AdsSettingsSerializer, AdVideoSerializer, AdWatchSerializer
from .services import (
    complete_watch_ad,
    get_ads_history,
    get_ads_status,
    get_daily_ads_payout,
    get_monthly_ads_payout,
    start_watch_ad,
)


class MyAdsStatusView(APIView):
    def get(self, request):
        return Response(get_ads_status(request.user))


class MyAdsWatchStartView(APIView):
    def post(self, request):
        try:
            watch, video, settings = start_watch_ad(request.user)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(
            {
                "watchId": watch.id,
                "video": {
                    "id": video.id,
                    "title": video.title,
                    "url": video.video.url if video.video else None,
                    "durationSeconds": video.duration_seconds,
                },
                "rewardPerAd": (
                    settings.welcome_reward_pkr if watch.cycle and watch.cycle.cycle_type == "welcome" else settings.pair_reward_pkr
                ),
            }
        )


class MyAdsWatchCompleteView(APIView):
    def post(self, request, pk):
        try:
            complete_watch_ad(request.user, pk)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(get_ads_status(request.user))


class MyAdsHistoryView(APIView):
    def get(self, request):
        return Response(get_ads_history(request.user))


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
        rows = AdWatch.objects.filter(status="completed").select_related("user", "cycle").order_by("-created_at")
        user_id = request.query_params.get("userId")
        if user_id:
            rows = rows.filter(user_id=user_id)
        return Response(AdWatchSerializer(rows[:500], many=True).data)


class AdminAdsVideosView(APIView):
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        rows = AdVideo.objects.all().order_by("-created_at")
        return Response(AdVideoSerializer(rows, many=True, context={"request": request}).data)

    def post(self, request):
        if not request.FILES.get("video"):
            return Response({"detail": "A video file is required."}, status=400)
        serializer = AdVideoSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)


class AdminAdsVideoDetailView(APIView):
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, pk):
        video = AdVideo.objects.filter(pk=pk).first()
        if video is None:
            return Response({"detail": "Video not found."}, status=404)
        serializer = AdVideoSerializer(video, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        video = AdVideo.objects.filter(pk=pk).first()
        if video is None:
            return Response({"detail": "Video not found."}, status=404)
        video.delete()
        return Response(status=204)


class AdminAdsDailyPayoutView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        day_param = request.query_params.get("date")
        day = date.fromisoformat(day_param) if day_param else None
        return Response(get_daily_ads_payout(day))


class AdminAdsMonthlyPayoutView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return Response(get_monthly_ads_payout(request.query_params.get("month")))
