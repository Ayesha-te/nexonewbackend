from django.urls import path

from .views import (
    AdminAdsDailyPayoutView,
    AdminAdsHistoryView,
    AdminAdsMonthlyPayoutView,
    AdminAdsSettingsView,
    AdminAdsVideoDetailView,
    AdminAdsVideosView,
    MyAdsHistoryView,
    MyAdsStatusView,
    MyAdsWatchCompleteView,
    MyAdsWatchStartView,
)

urlpatterns = [
    path("me/status/", MyAdsStatusView.as_view()),
    path("me/watch/start/", MyAdsWatchStartView.as_view()),
    path("me/watch/<int:pk>/complete/", MyAdsWatchCompleteView.as_view()),
    path("me/history/", MyAdsHistoryView.as_view()),
    path("admin/settings/", AdminAdsSettingsView.as_view()),
    path("admin/history/", AdminAdsHistoryView.as_view()),
    path("admin/videos/", AdminAdsVideosView.as_view()),
    path("admin/videos/<int:pk>/", AdminAdsVideoDetailView.as_view()),
    path("admin/payout/daily/", AdminAdsDailyPayoutView.as_view()),
    path("admin/payout/monthly/", AdminAdsMonthlyPayoutView.as_view()),
]
