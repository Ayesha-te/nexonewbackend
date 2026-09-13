from django.urls import path

from .views import (
    AdminAdsHistoryView,
    AdminAdsSettingsView,
    MyAdsStatusView,
    MyAdsWatchView,
)

urlpatterns = [
    path("me/status/", MyAdsStatusView.as_view()),
    path("me/watch/", MyAdsWatchView.as_view()),
    path("admin/settings/", AdminAdsSettingsView.as_view()),
    path("admin/history/", AdminAdsHistoryView.as_view()),
]
